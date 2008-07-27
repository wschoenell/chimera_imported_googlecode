from chimera.core.version   import _chimera_version_, _chimera_description_
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.location import Location, InvalidLocationException
from chimera.core.systemconfig import SystemConfig
from chimera.core.manager import Manager
from chimera.controllers.site.main import SiteController
from chimera.core.exceptions import ObjectNotFoundException
from chimera.core.path import ChimeraPath

from chimera.util.enum      import Enum

import sys
import optparse
import os.path

__all__ = ['ChimeraCLI',
           'action',
           'parameter']

ParameterType = Enum("INSTRUMENT", "DRIVER", "CONTROLLER", "BOOLEAN")

class Action (object):
    name   = None

    short = None
    long  = None

    type  = None
    default = None

    help  = None
    group = None
    metavar = None

    target = None
    cls = None
    instrument= None

    def __init__ (self, **kw):

        for key, value in kw.items():

            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise TypeError("Invalid option '%s'." % key)

        self.validate()

    def validate (self):

        self.name  = self.name or getattr(self.target, '__name__', None)

        if not self.name:
            raise TypeError("Option must have a name")

        self.long  = self.long or self.name
        self.help  = self.help or getattr(self.target, '__doc__', None)

        if self.short and self.short[0] != '-':
            self.short = "-" + self.short

        if self.long and self.long[0] != '-':
            self.long = "--" + self.long

        if self.name and self.name[0] == '-':
            self.name = self.name[self.name.rindex('-')+1:]

        if self.help:
            self.help = self.help.strip().replace("\n", " ")
            if self.default:
                self.help += " [default=%default]"

        if self.metavar:
            self.metavar = self.metavar.upper()
        else:
            self.metavar = self.name.upper()

    def __str__ (self):
        s = ""
        s += "<%s " % self.__class__.__name__
        for name in dir(self):
            attr = getattr(self, name)
            if not name.startswith("_") and not hasattr(attr, '__call__'):
                s += "%s=%s " % (name, attr)
        s = s[:-1]
        s += ">"
        return s

    def __repr__ (self):
        return self.__str__()

class Parameter (Action):
    pass


def action(*args, **kwargs):
    """
    Defines a command line action with short name 'short', long name
    'long'. If 'short' not given, will use the first letter of the
    method name (if possible), if 'long' not given, use full method
    name.

    Use 'type' if the action require a direct parameter, like '--to
    10', in this case, action should be like this:

    # @action(long='to', type='int')
    # def move_to (self, options):
    #     driver.moveTo(options.to)

    See L{Action} for information about valid keywork arguments.
    """

    def mark_action (func):
        kwargs["target"] = func
        act = Action(**kwargs)
        func.__payload__ = act
        return func

    if len(args) > 0:
        return mark_action(args[0])
    else:
        return mark_action


def parameter(*args, **kwargs):
    """
    Defines a command line parameter with short name 'short', long
    name 'long'. If 'short' not given, will use the first letter of
    the method name (if possible), if 'long' not given, use full
    method name. If type given, parameter will be checked to match
    'type'. The default value, if any, shoud be passed on 'default'.

    There are two specials parameter types: INSTRUMENT, DRIVER. They
    receive the same keyword arguments as normal parameters, but receive
    special treatment (detailed below in InstrumentDriverCheckers).

    See L{Parameter} for information about valid keywork arguments.
    """

    def mark_param (func):
        kwargs["target"] = func
        param = Parameter(**kwargs)
        func.__payload__ = param
        return func

    if len(args) > 0:
        return mark_param(args[0])
    else:
        return mark_param

class InstrumentDriverCheckers:

    @staticmethod
    def check_includepath (option, opt_str, value, parser):
        if not value or not os.path.isdir (os.path.abspath(value)):
            raise optparse.OptionValueError ("Couldn't found %s include path." % value)
        l = getattr(parser.values, "%s" % option.dest)
        l.append(value)

    @staticmethod
    def check_location (option, opt_str, value, parser):
        try:
            l = Location (value)
        except InvalidLocationException:
            raise optparse.OptionValueError ("%s isnt't a valid location." % value)

        setattr(parser.values, "%s" % option.dest, value)


class ChimeraCLI (object):
    """
    Create a command line program with automatic parsing of actions
    and parameters based on decorators.

    This class define common methods for a command line interface
    (CLI) program. You should extends it and add methods with specific
    decorators to create personalized CLI programs.

    This class defines a CLI program which accepts parameters (of any
    kind) and do actions using those parameters. Only one action will
    run for a given command line. if more than one action was asked,
    only the first will run.

    The general form of the arguments that CLI accepts is given
    below:

    cli-program (--action-1|--action-2|...|--action-n)
                [--param-1=value1,--param-2=value-2|...|--param-n=value-n]

    Al parameters are optional, action code will check for required
    parameters and shout if needed.

    At least one action is required, if none given, --help will be
    fired.

    There are a few auto-generated options:
     --help --quiet --verbose (default=True) --log=file

    To create actions, use 'action' decorator. If that action was
    detected on the command line arguments, action method will be
    called with an object containing all the parameters available.

    For example:

    @action(short='s', long='slew'):
    def slew(self, options):
        driver.slew(options.ra, options.dec)

    To define parameters, use parameter decorator or addParameter method.
    The parameter method passed to the decorator will be called to validate
    the parameter value given on the command line. Otherwise, no
    validation, besides type checking, will be done.

    For example:

    self.addParameter(name='ra', help='Help for RA', type=string)

    or

    @parameter(long='ra', type=string)
    def ra(self, value):
        '''
        Help for RA
        '''
        # validate
        # return valid value or throw ValueError

    When you define a Parameter using @parameter decorator,
    the name of the decorated function will be available in the options
    dictionary passed to every action. Otherwise, you need to use name
    keyword to define different names or to use with attribute based parameters

    Before run the selected action, ChimeraCLI runs the method
    __start__, passing all the parameters and the action that would
    run. After the action be runned, __stop__ would be called.

    """

    def __init__ (self, prog, description, version,
                  verbosity=True, sysconfig=True,
                  driver_path=True, instrument_path=True, controllers_path=True):

        self.parser = optparse.OptionParser(prog=prog,
                                             description=_chimera_description_ + " - " + description,
                                             version="Chimera: %s\n%s: %s" % (_chimera_version_, prog, version))

        self.options = None

        self._actions = {}
        self._parameters = {}
        self._groups = {}

        # base actions and parameters

        if verbosity:
            self.addParameters(dict(name="quiet", short="q", long="quiet",
                                    type=ParameterType.BOOLEAN, default=False,
                                    help="Don't display information while working."),

                               dict(name="verbose", short="v", long="verbose",
                                    type=ParameterType.BOOLEAN, default=True,
                                    help="Display information while working"))

        if sysconfig:
            self.addGroup("SYSCONFIG", "System Configuration")

            self.addParameters(dict(name="sysconfig", type=str, default=SYSTEM_CONFIG_DEFAULT_FILENAME,
                                    group="SYSCONFIG", help="Where to look for system congiguration."),
                               dict(name="nosysconfig", long="no-sysconfig", default=False,
                                    group="SYSCONFIG", help="Do not look for the system configuration file."))

#                               dict(name="host", short="H", group="SYSCONFIG", default="guessed from sysconfig",
#                                    help="Host name/IP where to look for Chimera"),
#                               dict(name="port", short="P", group="SYSCONFIG", default="guessed from sysconfig",
#                                    help="Port on which to to run instrument under when using local manager"))

            self.addActions()

        self.localManager = None
        self.sysconfig    = None

    def out(self, msg):
        sys.stdout.write(msg)
        sys.stdout.flush()

    def err(self, msg):
        sys.stderr.write(msg)
        sys.stderr.flush()

    def exit(self, msg, ret=1):
        self.__stop__(self.options)
        self.err(msg)
        sys.exit(ret)

    def addParameters(self, *params):
        for param in params:
            p = Parameter(**param)
            self._parameters[p.name] = p

    def addActions(self, *actions):
        for action in actions:
            act = Action(**action)
            self._actions[act.name] = act

    def addGroup(self, name, shortdesc, longdesc=None):
        self._groups[name] = optparse.OptionGroup(self.parser, shortdesc, longdesc)

    def addInstrument (self, **params):
        params["type"] = ParameterType.INSTRUMENT
        params["group"] = "SYSCONFIG"
        self.addParameters(params)

    def addDriver (self, **params):
        params["type"] = ParameterType.DRIVER
        params["group"] = "SYSCONFIG"
        self.addParameters(params)

    def addController (self, **params):
        params["type"] = ParameterType.CONTROLLER
        params["group"] = "SYSCONFIG"
        self.addParameters(params)

    def run (self, cmdlineArgs):

        # create parser from defined actions and parameters
        self._createParser()

        # run the parser
        self.options, args = self.parser.parse_args(cmdlineArgs)

        # check which action should run and if there is any conflict
        action = self._getAction(self.options)

        if not action:
            self.exit("More than one action requested. Please select only one.")

        # for each defined parameter, run validation code
        self._validateParameters(self.options)

        # start local manager, getting information from sysconfig
        self._startSystem(self.options)

        # setup objects
        self._setupObjects(self.options)

        self.__start__(self.options, args)

        # run actions
        ret = self._runAction(action, self.options)

        self.__stop__(self.options)

    def _startSystem (self, options):

        sysconfig = None

        if not options.nosysconfig:
            sysconfig = SystemConfig.fromFile(options.sysconfig)

        localManager = Manager(host='localhost', port=9000)

        # check if the Manager specified on sysconfig is up, if not, start it
        if sysconfig:
            try:
                remoteManager = localManager.getProxy("%s:%d/Manager/0" % (sysconfig.chimera["host"],
                                                                           sysconfig.chimera["port"]))
                remoteManager.ping()
            except ObjectNotFoundException:
                localManager.shutdown()

                # FIXME: better way to start Chimera
                args = "-f %s" % options.sysconfig
                site = SiteController(args.split(), wait=False)
                site.startup()

                localManager = site.manager

        self.sysconfig = sysconfig
        self.localManager = localManager

    def _setupObjects (self, options):

        # CLI requested objects (Action objects)
        drivers     = dict([(x.name, x) for x in self._parameters.values() if x.type == ParameterType.DRIVER])
        instruments = dict([(x.name, x) for x in self._parameters.values() if x.type == ParameterType.INSTRUMENT])
        controllers = dict([(x.name, x) for x in self._parameters.values() if x.type == ParameterType.CONTROLLER])

        # process inst/driver pairs
        for inst in instruments.values():

            new_local_driver = False

            inst_loc = None
            drv_loc = None

            inst_proxy = None
            drv_proxy = None

            drv = [d for d in drivers.values() if d.instrument == inst.name]
            # uses only the first driver (if more found)
            if drv: drv = drv[0]
            assert drv != None, "Parser error. Instrument without a driver!"

            if inst.default != getattr(options, inst.name):
                inst_loc = Location(getattr(options, inst.name))

            if drv.default != getattr(options, drv.name):
                drv_loc = Location(getattr(options, drv.name))

            if not inst_loc:
                if self.sysconfig:
                    inst_loc = [i for i in self.sysconfig.instruments if i.cls == inst.cls]
                    if inst_loc: inst_loc = inst_loc[0]
                else:
                    self.exit("Couldn't found %s configuration. Edit chimera.config or see --help for more information\n" % inst.name.capitalize())

            if drv_loc:

                try:
                    drv_proxy = self.localManager.getProxy(drv_loc)
                except ObjectNotFoundException:
                    pass

                if not drv_proxy:
                    if self.localManager._belongsToMe(drv_loc):
                        drv_proxy = self.localManager.addLocation(drv_loc, start=True,
                                                                  path=ChimeraPath.drivers())
                        new_local_driver = True
                    else:
                        self.exit("Couldn't found driver %s.\n" % drv_loc)

            if inst_loc:

                try:
                    inst_proxy = self.localManager.getProxy(inst_loc)
                except ObjectNotFoundException:
                    pass

                if inst_proxy:

                    if drv_proxy:

                        if not inst_proxy["driver"] == drv_proxy.getLocation():
                            if not new_local_driver:
                                self.exit("Couldn't change %s driver to %s. "
                                          "The %s is already running.\n" % (inst_loc, drv_loc,
                                                                            inst.name.capitalize()))
                            else:
                                # force local instrument
                                inst_loc = Location(name=inst.cls, name="local_instrument")
                                inst_loc._config.update({"driver": str(drv_loc)})
                                inst_proxy = self.localManager.addLocation(inst_loc,
                                                                           start=True,
                                                                           path=ChimeraPath.instruments())
                else:

                    if self.localManager._belongsToMe(inst_loc):
                        inst_loc._config.update({"driver": str(drv_loc)})
                        inst_proxy = self.localManager.addLocation(inst_loc, start=True,
                                                                   path=ChimeraPath.instruments())
                    else:
                        self.exit("Couldn't found %s (%s).\n" % (inst.name.capitalize(), inst_loc))


            #print "inst location:", inst_loc, "drv location:", drv_loc
            #print "inst proxy   :", inst_proxy, "drv proxy:", drv_proxy
            #print

            if not inst_proxy and not drv_proxy:
                self.exit("Couldn't found %s configuration, Edit %s or "
                          "pass instrument/driver parameters (see --help)\n" % (inst.name.capitalize(),
                                                                                options.sysconfig))

            # save values in options
            if inst_proxy:
                setattr(options, inst.name, inst_proxy)

            if drv_proxy:
                setattr(options, drv.name, drv_proxy)

    def __start__ (self, options, args):
        pass

    def __stop__ (self, options):
        if self.localManager is not None:
            self.localManager.shutdown()

    def _createParser (self):

        for name in dir(self):
            attr = getattr(self, name)

            if isinstance(attr, Action) or hasattr(attr, '__payload__'):

                try:
                    # decorated methods
                    payload = getattr(attr, '__payload__')
                except AttributeError:
                    # pure attribute
                    payload = attr

                if type(payload) == Action:
                    self._actions[payload.name] = payload
                elif type(payload) == Parameter:
                    self._parameters[payload.name] = payload

        for action in self._actions.values():

            if action.type:
                kind = "store"
            else:
                kind = "store_true"

            group = self._groups.get(action.group, self.parser)

            if action.short:
                group.add_option(action.short, action.long,
                                 action=kind, type=action.type, dest=action.name,
                                 help=action.help, metavar=action.metavar)
            else:
                group.add_option(action.long, dest=action.name,
                                 action=kind, type=action.type,
                                 help=action.help, metavar=action.metavar)

        for param in self._parameters.values():

            if not param.type:
                param.type = "string"

            group = self._groups.get(param.group, self.parser)

            option_action = "store"
            option_callback = None
            option_type = param.type or None

            if param.type in (ParameterType.INSTRUMENT, ParameterType.DRIVER, ParameterType.CONTROLLER):
                option_type = "string"
                option_action = "callback"
                option_callback  = InstrumentDriverCheckers.check_location

            if param.type == ParameterType.BOOLEAN:
                option_action = "store_true"
                option_type = None

            option_kwargs = dict(action=option_action,
                                 dest=param.name,
                                 help=param.help, metavar=param.metavar)

            if option_callback:
                option_kwargs["callback"] = option_callback

            if option_type:
                option_kwargs["type"] = option_type

            if param.short:
                group.add_option(param.short, param.long, **option_kwargs)
            else:
                group.add_option(param.long, **option_kwargs)

        for group in self._groups.values():
            self.parser.add_option_group(group)

        defaults = {}

        for action in self._actions.values():
            if action.default is not None:
                defaults[action.name] = action.default

        for param in self._parameters.values():
            if param.default is not None:
                defaults[param.name] = param.default

        self.parser.set_defaults(**defaults)

    def _getAction(self, options):

        actionValues = [ getattr(options, action) for action in self._actions.keys() ]

        actionToRun = False

        if not any(actionValues):
            self.exit("Please select one action or --help for more information.\n")

        for action, value in zip(self._actions.keys(), actionValues):

            if value and actionToRun: # conflict, more than one action selected
                return False

            if value:
                actionToRun = action

        return actionToRun

    def _validateParameters(self, options):

        paramValues =  [ getattr(options, param) for param in self._parameters.keys() ]

        for name, value in zip(self._parameters.keys(), paramValues):
            param = self._parameters[name]

            try:
                # to signal invalid values, use self.exit or throws a ValueError exception
                # if None returned, just copy passed value
                if param.target is not None:
                    newValue = getattr(self, param.target.__name__)(value)
                    setattr(options, name, newValue or value)
            except ValueError, e:
                self.exit("Invalid value for %s: %s\n" % (name, e))

    def _runAction(self, actionName, options):

        action = self._actions[actionName]

        try:
            if action.target is not None:
                getattr(self, action.target.__name__)(options)
        except Exception, e:
            self.err("Something wrong with '%s' action.\n" % (action.name))
            sys.excepthook(*sys.exc_info())
            return 1

        return 0
