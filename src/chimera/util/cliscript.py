
class CliScript (object):
    
    parser  = None
    options = None
    
    manager = None
    
    
    
    def check_includepath (option, opt_str, value, parser):
        if not value or not os.path.isdir (os.path.abspath(value)):
            raise optparse.OptionValueError ("Couldn't found %s include path." % value)
        eval ('parser.values.%s.append ("%s")' % (option.dest, value))

    def check_location (option, opt_str, value, parser):
        try:
            l = Location (value)
        except InvalidLocationException:
            raise optparse.OptionValueError ("%s isnt't a valid location." % value)

        eval ('parser.values.%s.append ("%s")' % (option.dest, value))


    parser = OptionParser(prog="chimera-tel", version=_chimera_version_,
                          description=_chimera_description_+chimera_tel_description)
    
        parser.add_option("-H", "--host", action="store", 
                          dest="pyro_host", type="string",
                          help="Host name/IP to connect to when using instrument "
                          "under remote management); [default=%default]",
                          metavar="HOST")
    
        parser.add_option("-P", "--port", action="store", 
                          dest="pyro_port", type="string",
                          help="Port on which to connect when using instrument "
                          "under remote management; [default=%default]",
                          metavar="PORT")
    
            parser.add_option("-q", "--quiet", action="store_true", dest='quiet',
                          help="Don't display informations while working [default=%default].")

        parser.set_defaults(telescope= [],
                            driver   = ["/Meade/meade?device=/dev/ttyS6"],
                            drv_dir  = [],
    
    
    
        parser.set_defaults(telescope= [],

                            pyro_host=MANAGER_DEFAULT_HOST,
                            pyro_port=MANAGER_DEFAULT_PORT)

    options, args = parser.parse_args(sys.argv)
    
        # ctrl+c handling
    aborted = False
    
    def ctrlHandler (self):

    def sighandler(self, sig = None, frame = None):

        global aborted
        
        if aborted == False:
            aborted = True
        else:
            return
            
        print >> sys.stdout, "aborting... ",
        sys.stdout.flush()

        def abort():
            tel = copy.copy(telescope)
            if tel.isSlewing():
                tel.abortSlew()

        t = threading.Thread(target=abort)
        t.start()
        t.join()
            
    signal.signal(signal.SIGTERM, sighandler)
    signal.signal(signal.SIGINT, sighandler)


    # action
    start = time.time()
    
    
    try:

    finally:
        telescope.slewBegin     -= slewBegin
        telescope.slewComplete  -= slewComplete

        manager.shutdown()

        if not options.quiet and not options.info:
            print 40*"="
            print "Total time: %.3fs" % (time.time()-start)
            print 40*"="

        sys.exit(0)
