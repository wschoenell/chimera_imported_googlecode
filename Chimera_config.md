Configuration files are read by chimera at startup and used to define all instruments and controllers used in the system.  If you create a new chimera object and want it to be used by the system, you must tell chimera about this object using the configuration file.

By default the configuration file resides in ~/.chimera/chimera.config  When running chimera one may specify an alternate config file using 'chimera --config=FILE'

# Introduction #

I will show a sample file describing all the instruments + controllers used in the Meade 40cm at OPD.

Then after discussing this example I go into some special cases of other configurations.


# Details #

The default location for the configuration file is in $HOME/.chimera/chimera.config

The parameters that can be defined here are declared in the class interface defining that instrument or controller, see for instance the autofocus interface:

```
    # set of parameters and their defaults
    __config__ = {"telescope"          : "/FakeTelescope/0",
                  "camera"             : "/FakeCamera/0",
                  "filterwheel"        : "/FilterWheel/0",
                  "tolra"              : 0.0166666666667,
                  "toldec"             : 0.0166666666667,
                  "exptime"            :  10.0,
                  "filter"             :  "R",
                  "max_trials"         :  10
```

The order is as is usual on unix programs: 1) command line; 2) configuration file; 3) code


```
[obs@minerva ~]$ cd .chimera/
[obs@minerva .chimera]$ more chimera.config
```

Here I say the chimera server is running on localhost (replace XXX.XXX.XXX.XXX by the real IP of your machine) on port 7666

```
chimera:
 host: XXX.XXX.XXX.XXX
 port: 7666
```

We are running two controllers on OPD, one is the imageserver which should run always.

The other autofocus runs only if you have a supported focuser

```
controllers:
 - type: ImageServer
   name: imageServer
   autoload: False

 - type: AutoFocus
   name: autoFocus
   camera: /SBIG/0
   focuser: /OptecTCFS/0
   filterwheel: /SBIG/0
```

Site is a special instrument and defines your, surprise, site:

```
site:
 name: LNA
 latitude: "-22:32:04"
 longitude: "-45:34:57"
 altitude: 1864
 utc_offset: -3
```


Telescope describes the telescope.  All the info below is useful:

  * device: serial port the telescope is attached to.
  * model: needed for the driver to know which commands to send to the scope
  * optics:
  * mount: remember there is a mount and an optical tube assembly.  We are packing these two things under the name of telescope
  * aperture:
  * focal\_length: used to compute plate scale (this goes in image headers and is used in pointVerify for instance
  * focal\_reduction: same as above

```
telescope:
 type: Meade
 name: meade
 device: /dev/ttyS6
 model: Meade 16 inch Classic
 optics: SCT
 mount: Meade
 aperture: 406.4
 focal_length: 4064
 focal_reduction: 1.0
```

The sbig st8 actually consists of two CCDs, so it is listed as two cameras, one we call st8, the other we call tracking, the camera configuration has some telescope parameters and filter wheel parameters

```
camera:
 - type: SBIG
   name: st8
   device: USB
   ccd: IMAGING
   telescope_focal_length: 4064 # mm
   filters: U B V R I
   filter_wheel_model: SBIG CFW8
   ccd_model: KODAK KAF1602E

 - type: SBIG
   name: tracking
   device: USB
   ccd: TRACKING
   telescope_focal_length: 4064 # mm
   filters: U B V R I
   filter_wheel_model: SBIG CFW8
   ccd_model: TI-TC237H
```


The only focuser we have a driver for at the moment
```
focuser:
 type: OptecTCFS
 name: optec
 device: /dev/ttyS4
```

The dome was custom built at LNA

```
dome:
 type: DomeLNA40cm
 name: dome
 device: /dev/ttyS9
 mode: Track
 telescope: /Meade/meade
 model: COTE/LNA
 style: Classic
```


Here is the UFSC telescope.  The main particularity of this setup is the telescope mount.  This mount is a paramount by software bisque.  As bisque wouldn't disclose their protocol to us we are forced to use their theSky software to control the mount.

The telescope instrument running on chimera on the linux machine talks to theSky under another chimera on a windows machine.

Here is the file with comments:

same as for LNA machine (replace XXX with your IP)

```
chimera:
  host: XXX.XXX.XXX.XXX
  port: 7666

site:
  name: UFSC
  latitude: "27:36:12.286"
  longitude: "-48:31:20.535"
  altitude: 20
  utc_offset: -3

camera:
  name: st7
  type: SBIG

  filters: "R G B RGB CLEAR"
```

Here is the special trick.  The class that controls the telescope is called "TheSkyTelescope".  This is not a local object it runs on a different machine and listens to some port.  By default the host part is left undeclared meaning it runs on the same host.  Note this can be done for any chimera object.

```
telescope:
  name: paramount
  type: TheSkyTelescope
  host: XXX.XXX.XXX.YYY
  port: 7666
```

Here is two controllers.

First is the ImageServer for which we specify save\_dir and load\_dir, unlike we did for the LNA telescope config file.

Then comes PointVerify.  There is an added complication here.  This guys' telescope parameter defaults to /Telescope/0 this however, does not work if your telescope is running on another machine.  So we need to state explicitly where the telescope is running.

```
controllers:
 - name: image_server
   type: ImageServer
   save_dir: "$HOME/images/$LAST_NOON_DATE"
   load_dir: "$HOME/images"
   autoload: False

 - name: pv
   type: PointVerify
   telescope: 150.162.110.3:7666/TheSkyTelescope/paramount
   exptime: 30
   filter: R
```