[TOC]

# Understanding the Universal Serial Bus (USB)

by Prof. Daniel Côté, Ph.D., P. Eng., dccote@cervo.ulaval.ca, http://www.dcclab.ca

You are here because you have an interest in programming hardware devices, and the communication with many of them is through the Universal Serial Bus, or USB. The USB standard is daunting to non-expert for many reasons:  because it is so general (universal), it needs to provide a solution to many, many different types of devices from mouse pointers to all-in-one printers, USB hubs, ethernet adaptors, etc. In addition, it was created to [solve problems related to the original serial port RS-232](README-RS232.md), and if you have not worked with old serial ports, some of the problems USB solves will not be apparent to you or may not even appear necessary. Therefore, when you are just trying to understand serial communications for your problem ("*I just want to send a command to my XYZ stage!*"), all this complexity becomes paralyzing.  Of course, you don't always need to program everything from scratch, like we will do here: very often, manufacturers will provide a Python Software Development Kit (or SDK) with all the work done for you. **If it exists, use it.** However, we assume here that either such an SDK is not available or you simply want to learn how they are made.  We could always sweep everything under the rug, but you are currently reading this document, so it is assumed you want to understand the details.  I hope to help you understand better from the perspective of a non-expert.

## Inspecting USB devices

Let's start by exploring with Python and PyUSB to see what these devices are telling us. We will not communicate with them directly yet, we will simply inspect them.

### Installing PyUSB and libusb

I wish we could dive right in.  I really do. If you just want to see what I do, skip and go to the exploration part ([First Steps](#first-steps)).  But if you want to explore on your computer too, then you need to install PyUSB and libusb.

The first part is simple. Install the PyUSB module with `pip`:

```sh
pip install pyusb
```

But then, you need to install `libusb`, which is the actual engine that talks to the USB ports on your computer, and PyUSB needs to know where it is. Libusb is an open source library that has been adopted by many developers because it is complete, bug-free and cross-platform, and without it, PyUSB will not work. Doing `pip install libusb` is not a solution, it is a different module and keeps the libusb "for itself". It also does not ship with the macOS libusb. You can use Zadig on Windows to install it or brew on macOS. It may also already be installed on your computer (if you see `/usr/local/lib/libusb-1.0.0.dylib` on your computer, it should work).  On macOS and Linux, install libusb with these two lines in the terminal:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install libusb
```

On Windows, get [Zadig](https://zadig.akeo.ie) and [keep for fingers crossed](https://github.com/libusb/libusb/wiki/Windows#how-to-use-libusb-on-windows). Worse comes to worst, the simplest solution is to [download](https://libusb.info) it and keep `libusb-1.0.x.dll` in the directory where you expect to keep your Python scripts (for now). Don't get me started on [DLLs on Windows](https://github.com/DCC-Lab/PyHardwareLibrary/commit/ddfaf442d61348d7ed8611f2436e43f20b450c45). If everything really does not work for one reason or another, you can use [USBView](https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/usbview) or [USBTreeView](https://www.uwe-sieber.de/usbtreeview_e.html) to at least look at the USB descriptors.

### First steps

Your computer has a USB bus, that is, a main entry point through which all USB devices that you connect will communicate. When you plug in a device, it will automatically provide basic information to identify itself. That information is hardcoded into the device and informs the computer what it is and what it can do. So the first thing we want is to list all devices currently connected to your computer through your USB bus (or busses, some computers have more than one):

```python
import usb.core
import usb.util

for bus in usb.busses():
    for device in bus.devices:
        if device != None:
            usbDevice = usb.core.find(idVendor=device.idVendor, 
                                      idProduct=device.idProduct)
            print(usbDevice)
```

I connected a Kensington Wireless presenter and Laser pointer.  I get the following **USB Device Descriptor**, which I commented for clarity:

```sh
DEVICE ID 047d:2012 on Bus 020 Address 001 =================
 bLength                :   0x12 (18 bytes)              # The length in bytes of this description
 bDescriptorType        :    0x1 Device                  # This is a USB Device Descriptor
 bcdUSB                 :  0x200 USB 2.0                 # What USB standard it complies to
 bDeviceClass           :    0x0 Specified at interface  # A class of device (here, not known yet)
 bDeviceSubClass        :    0x0                         # A subclass of device (here, not known yet)
 bDeviceProtocol        :    0x0                         # A device protocol (here, not known yet)
 bMaxPacketSize0        :    0x8 (8 bytes)               # The size of packets that will be transmitted
 idVendor               : 0x047d                         # The USB Vendor ID.  This is Kensington.
 idProduct              : 0x2012                         # The USB Product ID.  This pointer device.
 bcdDevice              :    0x6 Device 0.06              
 iManufacturer          :    0x1 Kensington              # The text description of the manufacturer
 iProduct               :    0x3 Wireless Presenter with Laser Pointer # Text name of product
 iSerialNumber          :    0x0                         # The text description of the serial number 
 bNumConfigurations     :    0x1                         # The number of USB configurations

```

Let's highlight what is important:

1. First: numbers written 0x12, 0x01 etc... are hexadecimal numbers, or numbers in base 16. Each "digit" can take one of 16 values: 0-9, then a to f representing 10 to 15. Therefore,  0x12 is 1 x 16 + 2 = 18 dec.  Lowercase or uppercase are irrelevant.  Up to 9, decimal and hexadecimal are the same.
2. The **vendor id** is unique to the vendor of this device.  This value is registered with the USB consortium for a small cost. In the present case, we can use this later to get "all devices from Kensington".
3. The **product id** is unique to a product, from Kensington.  The vendor manages their product ids as they wish.
4. The **bNumConfigurations** is the number of possible configurations this USB device can take. It will generally be 1 with scientific equipment, but it can be more than that. We will simply assume it is always 1 for the rest of the present discussion, this is not a vital part for us.
5. Don't worry about the letters (`b`, `i`, `bcd`) in front of the descriptors: they simply indicate without ambiguity how they are stored in the USB descriptor: a `b` represents a *byte* value, an `i` represents a *2-byte integer*, and a `bcd` is also a 2-byte integer, but interpreted in decimal (binary-coded-decimal). `bcdUSB`= 0x200 means 2.0.0.
6. You may be wondering how a string can be represented by an integer (say `iManufacturer`)? This is because it is not the string itself, but a string pointer to a list of strings at the end of the descriptor.  PyUSB automatically fetches the corresponding string when showing show the descriptor.

Right after connecting, the device is in an "unconfigured mode". Someone, somewhere, needs to take responsibility for this device and do something.  Again, we need to separate general user devices (mouse, printers etc...) from scientific hardware.  With user devices, the device class, subclass, vendor id, product id, and protocol are sufficient for the computer to determine whether or not it can manage it. If the computer has the driver for this device, it will "own" it and manage it.  For instance, the printer is recognized and then the operating system can do what it needs to do with it (this is [discussed below](#communicating-with-usb-devices)).  However, scientific equipement will often appear as "General Device", and the computer will likely not know what to do.  This is when we come in.

### Configuring the USB device

We need to set the device into one of its configurations.  As described before, this is most likely just setting the device in its only possible configuration. So we get the USB device using the `usb.core.find` function of PyUSB, which will just relay the request to libusb and return any device that matches the parameters we want. In our case, we specify the idVendor and the idProduct, so the only device that can match is the one we want.

```python
import usb.core
import usb.util

device = usb.core.find(idVendor=0x047d, idProduct=0x2012)  # For a Kensington pointer. Choose yours.
if device is None:
	raise IOError("Can't find device")

device.set_configuration()                        # Use the first configuration
configuration = device.get_active_configuration() # Then get a reference to it
print(configuration)
```

This will print the following **USB Configuration Descriptor**, which I am also commenting:

```sh
  CONFIGURATION 1: 100 mA ==================================
   bLength              :    0x9 (9 bytes)
   bDescriptorType      :    0x2 Configuration        # This is a USB Configuration descriptor
   wTotalLength         :   0x22 (34 bytes)
   bNumInterfaces       :    0x1                      # It has one "USB interface" (discussed below)
   bConfigurationValue  :    0x1                      # It is configuration number 1 (there is no 0).
   iConfiguration       :    0x0 
   bmAttributes         :   0xa0 Bus Powered, Remote Wakeup
   bMaxPower            :   0x32 (100 mA)
[... more stuff related to interfaces and endpoints ... ]
```

Again, the important aspects.

1. It has a configuration value of 1, which happens to be the only one. Notice that it starts at 1, not 0. 

   *In fact, some devices in the wild are distributed with a single configuration labelled '0'. This is invalid according to the standard because `set_configuration(0)` is the method to unconfigure a device and `0` is the value returned when the device is unconfigured, but nevertheless still occurred.  For a while, since it was so common, Microsoft and Apple had a workaround and still accepted 0 as a valid configuration number but around 2020 (Windows 10 and Catalina I believe), both companies stopped doing that and required changes in the devices (which is hard: this is hardcoded in the device).*

2. It says it has one **USB Interface.**  This is discussed below.

3. The configuration has some technical details, such as the fact it does not need extra power and will require 100 mA or less when connected.

### Choosing a USB interface

The best way to understand **USB interfaces** is to use an example everyone knows: all-in-one printers.  These printers-scanners can act like a printer or a scanner, yet they have a single USB cable. Sometimes they will act like a printer, sometimes they will act like a scanner, and nothing says they can't do both at the same time. The **USB Interface** is the front face or appearance of the device to the computer: the device offers a "printer interface" and a "scanner interface" and depending on what you want to do, you will choose the one you need. So this device has a single interface, let's look at it.  The above code also prints information about the interfaces of the configuration, but I had removed them for simplicity. Here is the **USB Interface Descriptor**:

```python
    INTERFACE 0: Human Interface Device ====================
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface              # This is a USB Interface Descriptor
     bInterfaceNumber   :    0x0                        # It has interface number 0. It starts at 0 not 1
     bAlternateSetting  :    0x0                        
     bNumEndpoints      :    0x1                        # It has a single user-endpoint (will be number 1)
     bInterfaceClass    :    0x3 Human Interface Device # It is a type of Human Device (i.e. manipulatable)
     bInterfaceSubClass :    0x1                        # Can be available on boot
     bInterfaceProtocol :    0x1                        # 1: keyboard, 2: mouse
     iInterface         :    0x0 
[ ... more stuff about endpoints ....]
```

In this particular situation (a Kensington laser pointer), there is a single interface: 

1. The **bInterfaceClass** (0x03) says that if you choose interface #0, then you will be speaking to a Human Interface Device, which typically means keyboard, mouse, etc...  The **bInterfaceSubClass** and protocol are sufficient for the computer to determine whether or not it can manage it.  In this case, the **bInterfaceProtocol** says it acts like a keyboard.  
2. We don't need to dig deeper in Human Interface Devices at this point, but the computer will communicate with the device with accepted protocols on endpoint 0 (the "hidden", but mandatory Control Endpoint 0).
3. Some devices (in fact, most scientific equipment) will be "*serializable*".  When this information is included in the USB Interface Descriptor, the system will have sufficient information to create a virtual serial port.  At that point, the device will "appear" as a regular serial device (COM on Windows, `/dev/cu.*` on macOS and Linux). You can then connect to it like an old-style serial port just like the good ol'days with bauds, stop bits and parity, possible handshakes and all (this is a [separate discussion](README-232.md)).

### Viewing input and output endpoints

Finally, each USB interface has communication channels, or **endpoints**, that it decides to define for its purpose. An endpoint is a one-way communication either to the device (OUT) or into the computer (IN).  This Kensington Pointer has a single input enpoint, which means we cannot "talk" to it, we can only "read" from it.  Its **USB Endpoint Descriptor** is the following:

```sh
      ENDPOINT 0x81: Interrupt IN ==========================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint     # This is a USB Endpoint Descriptor
       bEndpointAddress :   0x81 IN           # Input (because of the 0x80) and number 1.
       bmAttributes     :    0x3 Interrupt    # It is an interrupt endpoint
       wMaxPacketSize   :    0x8 (8 bytes)    # Transmists 8 bytes at a time
       bInterval        :    0xa              # Describes how fast the data will come in.

```

The important take home points are:

1. The interface will define user-endpoints (that is, endpoints that the programmer can use to talk to the device).  There are also two implicit (hidden) endpoints called endpoint #0, or the Control Endpoints. These are used to communicate "control" and USB information to the device and for our purpose (we are not making the USB chips that communicates with the device, we only want to talk to the device), then we won't need to worry about it.  We just need to know it's there.  For this reason, endpoints are numbered starting at #1.

2. You can have Endpoint #1 IN and Endpoint #1 OUT, they are different endpoints.

3. The endpoints can communicate information in various ways, and most of the time we do not care so much how it does so. Here we have an **INTERRUPT** endpoint that will provide information to the computer whenever needed. Because it is a keyboard/mouse, so we want to be responsive: it will typically refresh the position or the keys at 100 Hz.

4. My Logitech mouse has a very similar USB Device Descriptor with very similar parameters, aside from the fact that it delivers only 4 bytes of information each time :

   ```sh
   DEVICE ID 046d:c077 on Bus 020 Address 002 =================
    bLength                :   0x12 (18 bytes)
    bDescriptorType        :    0x1 Device
    bcdUSB                 :  0x200 USB 2.0
    [...]
    idVendor               : 0x046d                 # Logitech 
    idProduct              : 0xc077                 # An old optical mouse
    bcdDevice              : 0x7200 Device 114.0
   [ ... ]
     bNumConfigurations     :    0x1
     CONFIGURATION 1: 100 mA ==================================
      bLength              :    0x9 (9 bytes)
      bDescriptorType      :    0x2 Configuration
   [ ... ]
      bNumInterfaces       :    0x1
      bConfigurationValue  :    0x1
   [ ... ]
       INTERFACE 0: Human Interface Device ====================
        bInterfaceNumber   :    0x0
        bNumEndpoints      :    0x1
        bInterfaceClass    :    0x3 Human Interface Device
        bInterfaceSubClass :    0x1                 # Available on boot
        bInterfaceProtocol :    0x2                 # This is a mouse, not a keyboard
         ENDPOINT 0x81: Interrupt IN ==========================
          bLength          :    0x7 (7 bytes)
          bDescriptorType  :    0x5 Endpoint
          bEndpointAddress :   0x81 IN
          bmAttributes     :    0x3 Interrupt
          wMaxPacketSize   :    0x4 (4 bytes)       # Only 4 bytes are delivered each time
          bInterval        :    0xa
   ```

   

Finally, here is the complete **USB Device Descriptor** for my HP Envy all-in-one printer:

```sh
DEVICE ID 03f0:c511 on Bus 020 Address 001 =================
 bLength                :   0x12 (18 bytes)
 bDescriptorType        :    0x1 Device
 bcdUSB                 :  0x200 USB 2.0
 bDeviceClass           :    0x0 Specified at interface     # The class depends on the interface selected
 bDeviceSubClass        :    0x0
 bDeviceProtocol        :    0x0
 bMaxPacketSize0        :   0x40 (64 bytes)
 idVendor               : 0x03f0
 idProduct              : 0xc511
 bcdDevice              :  0x100 Device 1.0
 iManufacturer          :    0x1 HP
 iProduct               :    0x2 ENVY 4500 series
 iSerialNumber          :    0x3 CN47Q1329D05X4
 bNumConfigurations     :    0x1
  CONFIGURATION 1: 2 mA ====================================
   bLength              :    0x9 (9 bytes)
   bDescriptorType      :    0x2 Configuration
   wTotalLength         :   0x9a (154 bytes)
   bNumInterfaces       :    0x3
   bConfigurationValue  :    0x1
   iConfiguration       :    0x0 
   bmAttributes         :   0xc0 Self Powered
   bMaxPower            :    0x1 (2 mA)
    INTERFACE 0: Vendor Specific ===========================
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x0
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x3
     bInterfaceClass    :   0xff Vendor Specific               # The vendor is using its own protocol
     bInterfaceSubClass :   0xcc                               # which you may know or not. I am guessing
     bInterfaceProtocol :    0x0                               # this is the scanner part
     iInterface         :    0x0 
      ENDPOINT 0x1: Bulk OUT ===============================   # 3 endpoints: bulk in/out and interrupt
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :    0x1 OUT
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
      ENDPOINT 0x82: Bulk IN ===============================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x82 IN
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)
       bInterval        :    0x0
      ENDPOINT 0x83: Interrupt IN ==========================
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x83 IN
       bmAttributes     :    0x3 Interrupt
       wMaxPacketSize   :   0x40 (64 bytes)
       bInterval        :    0x7
[ ... ]
    INTERFACE 1: Printer ===================================   
     bLength            :    0x9 (9 bytes)
     bDescriptorType    :    0x4 Interface
     bInterfaceNumber   :    0x1
     bAlternateSetting  :    0x0
     bNumEndpoints      :    0x2                               # Two endpoints
     bInterfaceClass    :    0x7 Printer                       # This is a printer interface
     bInterfaceSubClass :    0x1                               
     bInterfaceProtocol :    0x2
     iInterface         :    0x0 
      ENDPOINT 0x8: Bulk OUT ===============================   # Endpoint number 8 OUT to the printer
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :    0x8 OUT
       bmAttributes     :    0x2 Bulk                          # This is a BULK endpoint
       wMaxPacketSize   :  0x200 (512 bytes)                   # Large 512 bytes each packet
       bInterval        :    0x0
      ENDPOINT 0x89: Bulk IN ===============================   # Endpoint number 9 IN from the printer
       bLength          :    0x7 (7 bytes)
       bDescriptorType  :    0x5 Endpoint
       bEndpointAddress :   0x89 IN
       bmAttributes     :    0x2 Bulk
       wMaxPacketSize   :  0x200 (512 bytes)                   # Large 512 bytes each packet
       bInterval        :    0x0

```

Important highlights:

1. As you can see, some USB devices can provide several interfaces and options with many endpoints.  I picked this example to highlight that the USB standard offers a really general solution for device communication, and this is why it was designed and widely accepted upon introduction. 
2. There are different types of endpoints: INTERRUPT, BULK, ISOCHRONOUS. **Bulk** is what we could call a "standard" communication channel for us, experimentalists, trying to make things work.  For the most part, we don't really need to worry about it: we will communicate with our devices and get replies.
3. Here, having all this information about my printer is not really helping me communicate with it, because I don't know what commands it will accept. This information may or may not be proprietary, and without it, there is very little hope to "program" the printer directly.

### Final words

So for a hardware programmer who wants to use a USB device, the procedure will typically be like this:

1. Find the information specific about the device you want to use, so you can find it on the bus (idProduct, idVendor, etc...).
2. Get the **USB Device Descriptor**, configure it, typically with its only **USB Configuration**.
3. Pick a **USB Interface** (in scientific equipment, there is also often only one).
4. With the **USB interface** and PyUSB, you can then use **USB Endpoints** to send (OUT) or read (IN) commands.
   1. To do so, you will need to know the details from the manufacturer.  Typically, they will tell you : "Send your commands to Endpoint 1" and "Read your replies from endpoint 2". For instance, Ocean Insight makes spectrometers and the [manual](https://github.com/DCC-Lab/PyHardwareLibrary/blob/master/hardwarelibrary/manuals/USB2000-OEM-Data-Sheet.pdf) is very clear: on page 11, it says that there are two endpoint groups (IN and OUT) number 2 and 7. Each command described in the following pages tells you where to send your command and where to read the replies from. That is a good manual from a good company that likes its users.
   2. Some companies will not provide you with the endpoints information and will just provide a list of commands for their device (assuming you will talk through the regular serial interface).  You can experiment with endpoints relatively easily to figure out which is which for simple devices. For instance, a powermeter will typically have only one IN and one OUT endpoint, so it is easy to figure out what to do.

I have not said much about *actually* communicating with devices.  On your computer, drivers provided by Microsoft, Apple and others will go through a process to determine who controls a device when it is connected.  Your first project may be to try to read the keystrokes from your keyboard or the mouse position from your optical mouse, but that will not work:  when you connect your device, the operating system has a list of "generic drivers" that will take ownership of known devices, like a mouse, keyboard, printer, etc: that is the whole point of Plug-And-Play devices. The system reads the USBDescriptors, and other details and may be able to **match** a driver to your device.  If it does so, it will **claim** the exclusive use of the interface.  Hence, if you try to communicate with a device through an interface that was already claimed by the operating system (for example, your USB keyboard or mice),  you will get an error:

```
usb.core.USBError: [Errno 13] Access denied (insufficient permissions)
```

This of course is completely expected: two programs cannot send commands at the same time to a device through the same channels, the device would have no way of knowing what to do. In addition, *listening* to a keyboard for instance would be a major security flaw, and is not possible because the access for the device will be exclusive. Therefore, we will only be able to communicate with devices that the operating system has **not matched**. Many problems on Windows originate from this: an incorrect driver is installed and claims the device (erroneously).  You then have to remove the driver from the registry to avoid having a match that prevents the right driver from controlling the device.

You will find [many articles on the web](https://github.com/libusb/libusb/wiki/FAQ#running-libusb), that describe how to claim an interface that was already claimed. On Linux, [you can actually call](https://github.com/libusb/libusb/wiki/FAQ#can-i-run-libusb-application-on-linux-when-there-is-already-a-kernel-driver-attached-to-it) `libusb_detach_kernel_driver` that will unload the driver if you have sufficient permission (root). On the Mac, [this is done with](https://github.com/libusb/libusb/wiki/FAQ#how-can-i-run-libusb-applications-under-mac-os-x-if-there-is-already-a-kernel-extension-installed-for-the-device-and-claim-exclusive-access) `kextunload` (also as root, in the terminal) but I do not recommend it one bit because it will attempt to unload the kernel driver for all devices, not just your device.  Aside from the fact that this will likely fail, I really don't see a situation where this would be appropriate. Deleting the driver from the system is an even worse solution. *If it is already claimed, then there is probably a method to communicate with it through the regular means of the system.*

However,  scientific equipment is usually defined as a *vendor-specific device* with a *vendor-specific protocol*, therefore the system will rarely match and we will be able to have access to the USB interface and communicate with the device through the various endpoints. That's what we will do next.

## Communicating with USB devices

We may know how to identify a device, configure it, pick an interface and select communication channels, but then what? What does it imply to "program a device" ? What does it mean to "program a 3D stage" ? We will start with the easiest devices (those with a few commands), and then move on to more complicated devices (with binary commands and multiple endpoints).

The basic idea when we program a device is to send a command that the device recognizes (`move to 10,0,0`), it will perform the requested task (actually move), and then will reply (`Ok`). For many devices, controlling the device is just a series of request/reply until you are done. The work is therefore to send the right data down the endpoints to the device, and interpret the replies the device is sending.

### Encoding the information

The information is encoded in bytes. The bytes have different meaning depending on what were are sending. A letter is a single byte (8 bits) that can take 256 values from 0 to 255, or in hexadecimal `0x00` to `0xff`.  ASCII encoding is standard for text: in that system, the letter 'A' is the number 65 (0x41), 'C' is 67 (0x43) etc... To write integer numbers larger than 255, we can put more than one byte together. For instance, if we put 2 bytes together, we can get 65,536 different values (from `0x0000` to `0xffff`), if we use 4 bytes together, we can write 4,294,967,296 different values (from `0x00000000` to `0xffffffff`). These integers have names in Python: 1 byte is called a `char`acter, 2 bytes is a `short int` and 4 bytes is a `long int`.  It is possible to interpret these as `signed` or `unsigned`, where `signed` is usually the default if nothing else is mentionned. The detailed difference between `signed` and `unsigned` is not critical here, as long as we use the appropriate type.  When we start with the least significant bytes then the most significant, we say the format is "little-endian", otherwise it is "big-endian". You can find a bit more information [here](https://github.com/dccote/Enseignement/blob/master/DAQ/Semaine-02.md).

### An example: Sutter ROE-200

Let's look at a classic from microscopy and neuroscience, the MPC-385 XYZ stage from Sutter Instruments with its ROE-200 controller. The manual is available [here](https://github.com/DCC-Lab/PyHardwareLibrary/blob/cd7bf0cf6256ba4dbc6eb26f0657c0db59b35848/hardwarelibrary/manuals/MPC-325_OpMan.pdf) or on their web site, and it is sufficiently detailed for us (it also has a few omissions that we will find).  When we connect the device, we can inspect its **USB Descriptors**. We then find out that the idVendor is 4930, the idProduct is 1. We can pick a USB configuration, pick a USB interface, then the inspection of the endpoint descriptors tells us it has two endpoints: one IN, one OUT. 

```python
device = usb.core.find(idVendor=4930, idProduct=1) # Sutter Instruments has idVendor 4930 or 0x1342
if device is None:
    raise IOError("Can't find device")

device.set_configuration()                         # first configuration
configuration = device.get_active_configuration()  # get the active configuration
interface = configuration[(0,0)]                   # pick the first interface (0) with no alternate (0)

outputEndpoint = interface[0]                      # First endpoint is the output endpoint
inputEndpoint = interface[1]                       # Second endpoint is the input endpoint

```

### Commands

It is a very simple device, because it has a very limited set of commands it accepts. It can **move**, it can tell you its **position**.  There are other commands, but they will not be critical here and we will not implement them.

<img src="README.assets/image-20210415195905341.png" alt="image-20210415195905341" style="zoom:25%;" /><img src="README.assets/image-20210415195013040.png" alt="image-20210415195013040" style="zoom: 24%;" />

Let's look at the anatomy of the **Get Current Position** command: it is the `C` character (which has an ASCII code of 0x43), and the documentation says that the total number of bytes is two for the command. Reading other versions of the manual and discussing with Sutter tells us that all commands are followed by a carriage return `\r`  (ASCII character 0x0d). So if we send this command to the device, it should reply with its position.

The reply will be 13 bytes: it will consist of 3 values for X, Y and Z coordinates, encoded as `signed long integers` (32 bits or 4 bytes).  Closing this will be the carriage return `\r`, indicated at the top of the next page, for a total of 13 bytes.

### Sending GetPosition command

Python has `byte` and `bytearray` objects. The `b` indicates that the string of text must be interpreted as bytes. We pick the OUT endpoint, and send the command with:

```python
commandBytes = bytearray(b'C\r')
outputEndpoint.write(commandBytes)
```

### Reading GetPosition reply

We read the 13 bytes from the input endpoint:

```python
replyBytes = inputEndPoint.read(size_or_buffer=13)
```

If everything goes well, the last byte will be the character `\r`.  We know from the documentation that these 13 bytes represent 3 signed long integers and a character. Python has a function to `pack` and `unpack` this data. The function is described [here](https://docs.python.org/3/library/struct.html), and the format that corresponds to our binary data is `<lllc`: Little-endian (<), three long ('l') and a letter ('c') 

```python
x,y,z, lastChar = unpack('<lllc', replyBytes)

if lastChar == b'\r':
    print("The position is {0}, {1}, {2}".format(x,y,z))
else:
    print('Error in reply: last character not 0x0d')
   
```

### Sending MovePosition command

To move the stage to a different position, we need to encode (i.e. `pack`) the positions we want into binary data. This is done with:

```python
# We already have the position in x,y and z. We will move a bit from there.
commandBytes = pack('<clllc', ('M', x+10, y+10, z+10, '\r'))
outputEndpoint.write(commandBytes)
```

### Reading MovePosition reply

The stage will move and will send a `\r` when done, as per the documentation.

```python
replyBytes = inputEndPoint.read(size_or_buffer=1)
lastChar = unpack('<c', replyBytes)

if lastChar != b'\r':
    print('Error: incorrect reply character')
    
```

The complete code, repackaged with functions, is available here:

```python
# this file is called sutter.py
import usb.core
import usb.util
from struct import *

device = usb.core.find(idVendor=4930, idProduct=1) # Sutter Instruments has idVendor 4930 or 0x1342
if device is None:
    raise IOError("Can't find device")

device.set_configuration()                         # first configuration
configuration = device.get_active_configuration()  # get the active configuration
interface = configuration[(0,0)]                   # pick the first interface (0) with no alternate (0)

outputEndpoint = interface[0]                      # First endpoint is the output endpoint
inputEndpoint = interface[1]                       # Second endpoint is the input endpoint

def position() -> (int,int,int):
    commandBytes = bytearray(b'C\r')
    outputEndpoint.write(commandBytes)

    replyBytes = inputEndPoint.read(size_or_buffer=13)
    x,y,z, lastChar = unpack('<lllc', replyBytes)

    if lastChar == b'\r':
        return (x,y,z)
    else:
        return None
  
def move(position) -> bool:
    x,y,z  = position
    commandBytes = pack('<clllc', ('M', x, y, z, '\r'))
    outputEndpoint.write(commandBytes)
    
    replyBytes = inputEndPoint.read(size_or_buffer=1)
		lastChar = unpack('<c', replyBytes)

    if lastChar != b'\r':
        return True
    
    return False
    
```

## Encapsulating the USB device in a class

We may have communicated with the device, but it would still be tedious to use:

1. We will need to include this code in any Python script that manipulates the device
2. We have variables floating around (`device`, `interface`, `inputEndpoint`, `outputEndpoint`), they will prevent us from using them again (they are global).
3. We have to keep track of the position ourselves and convert to microns manually: currently the position is in micro steps
4. Our error management is minimal.  For instance, what if the device does not reply in time? 

It would be preferable to have a single object (i.e. the sutter device), and that that object 1) manages the communication without us, 2) responds to `moveTo` and `position`, 3) keeps track of its position, manage it and really, isolates us from the details? We don't really care that it communicates through USB and that there are "endpoints".  All we want is for the device to **move** and tell us **its position**.  We can therefore create a `SutterDevice` class that will do that: *a class hides the details away inside an object that keeps the variables and the functions to operate on these variables together.*

```python
# This file is called bettersutter.py
import usb.core
import usb.util
from struct import *

class SutterDevice:
    def __init_(self):
      self.device = usb.core.find(idVendor=4930, idProduct=1) 
			if device is None:
    		raise IOError("Can't find Sutter device")

      self.device.set_configuration()        # first configuration
      self.configuration = self.device.get_active_configuration()  # get the active configuration
      self.interface = self.configuration[(0,0)]  # pick the first interface (0) with no alternate (0)

      self.outputEndpoint = self.interface[0] # First endpoint is the output endpoint
      self.inputEndpoint = self.interface[1]  # Second endpoint is the input endpoint
      
      self.microstepsPerMicrons = 16

    def positionInMicrosteps(self) -> (int,int,int):
      commandBytes = bytearray(b'C\r')
      outputEndpoint.write(commandBytes)

      replyBytes = inputEndPoint.read(size_or_buffer=13)
      x,y,z, lastChar = unpack('<lllc', replyBytes)

      if lastChar == b'\r':
        return (x,y,z)
      else:
        return None
  
  	def moveInMicrostepsTo(self, position) -> bool:
      x,y,z  = position
      commandBytes = pack('<clllc', ('M', x, y, z, '\r'))
      outputEndpoint.write(commandBytes)

      replyBytes = inputEndPoint.read(size_or_buffer=1)
      lastChar = unpack('<c', replyBytes)

      if lastChar != b'\r':
        return True

      return False
    
    def position(self) -> (float, float, float):
			position = self.positionInMicrosteps()
      if position is not None:
          return (position[0]/self.microstepsPerMicrons, 
                  position[1]/self.microstepsPerMicrons,
                  position[2]/self.microstepsPerMicrons)
      else:
          return None
      
  	def moveTo(self, position) -> bool:
      x,y,z  = position
      positionInMicrosteps = (x*self.microstepsPerMicrons, 
                              y*self.microstepsPerMicrons,
                              z*self.microstepsPerMicrons)
      
      return self.moveInMicrostepsTo( positionInMicrosteps)

    def moveBy(self, delta) -> bool:
      dx,dy,dz  = delta
      position = self.position()
      if position is not None:
          x,y,z = position
          return self.moveTo( (x+dx, y+dy, z+dz) )
			return True

if __name__ == "__main__":
    device = SutterDevice()

    x,y,z = device.position()
    device.moveTo( (x+10, y+10, z+10) )
    device.moveBy( (-10, -10, -10) )
```

Notice how:

1. We don't know the implementation details, yet it fully responds to our needs: it can move and tell us where it is.
2. We can make other convenience functions that make use of the two key functions (`moveInMicrostepsTo` and `positionInMicrosteps`). For instance, we can create a `moveBy` function that will take care of getting the position for us then increase it and send the move command.
3. We still may have problems if the communication with the device does not go as planned.
4. If the device is not connected, or not on, the code will fail with no other options than to restart the program.



### Robust encapsulation

We can still improve things. In this version:

1. The device does not need to be connected for the `SutterDevice` to be created.

2. The write and read functions are limited to two functions that can manage any errors gracefully: if there is any error, we shutdown everything and will initialize the device again on the next call.

3. Minimal docstrings (Python inline help) is available.

   

```python
# This file is called bestsutter.py
import usb.core
import usb.util
from struct import *

class SutterDevice:
    def __init_(self):
      """
      SutterDevice represents a XYZ stage.  
      """
      self.device = None
      self.configuration = None
      self.interface = None
      self.outputEndpoint = None
      self.inputEndpoint = None
     
      self.microstepsPerMicrons = 16

    def initializeDevice(self):
      """
      We do a late initialization: if the device is not present at creation, it can still be
      initialized later.
      """

      if self.device is not None:
        return
      
      self.device = usb.core.find(idVendor=4930, idProduct=1) 
      if self.device is None:
        raise IOError("Can't find Sutter device")

      self.device.set_configuration()        # first configuration
      self.configuration = self.device.get_active_configuration()  # get the active configuration
      self.interface = self.configuration[(0,0)]  # pick the first interface (0) with no alternate (0)

      self.outputEndpoint = self.interface[0] # First endpoint is the output endpoint
      self.inputEndpoint = self.interface[1]  # Second endpoint is the input endpoint
    
    def shutdownDevice(self):
      """
      If the device fails, we shut everything down. We should probably flush the buffers also.
      """
      
      self.device = None
      self.configuration = None
      self.interface = None
      self.outputEndpoint = None
      self.inputEndpoint = None
      
    def sendCommand(self, commandBytes):
      """ The function to write a command to the endpoint. It will initialize the device 
      if it is not alread initialized. On failure, it will warn and shutdown."""
      try:
        if self.outputEndpoint is None:
          self.initializeDevice()
          
        self.outputEndpoint.write(commandBytes)
      except Exception as err:
        print('Error when sending command: {0}'.format(err))
        self.shutdownDevice()
    
    def readReply(self, size, format) -> tuple:
      """ The function to read a reply from the endpoint. It will initialize the device 
      if it is not already initialized. On failure, it will warn and shutdown. 
      It will unpack the reply into a tuple, and will remove the b'\r' that is always present.
      """

      try:
        if self.outputEndpoint is None:
          self.initializeDevice()

        replyBytes = inputEndPoint.read(size_or_buffer=size)
        theTuple = unpack(format, replyBytes)
        if theTuple[-1] != b'\r':
           raise RuntimeError('Invalid communication')
        return theTuple[:-1] # We remove the last character
      except Exception as err:
        print('Error when reading reply: {0}'.format(err))
        self.shutdownDevice()
        return None
      
    def positionInMicrosteps(self) -> (int,int,int):
      """ Returns the position in microsteps """
      commandBytes = bytearray(b'C\r')
      self.sendCommand(commandBytes)
      return self.readReply(size=13, format='<lllc')
  
    def moveInMicrostepsTo(self, position):
      """ Move to a position in microsteps """
      x,y,z  = position
      commandBytes = pack('<clllc', ('M', x, y, z, '\r'))
      self.sendCommand(commandBytes)
      self.readReply(size=1, format='<c')
    
    def position(self) -> (float, float, float):
      """ Returns the position in microns """

      position = self.positionInMicrosteps()
      if position is not None:
          return (position[0]/self.microstepsPerMicrons, 
                  position[1]/self.microstepsPerMicrons,
                  position[2]/self.microstepsPerMicrons)
      else:
          return None
      
    def moveTo(self, position):
      """ Move to a position in microns """

      x,y,z  = position
      positionInMicrosteps = (x*self.microstepsPerMicrons, 
                              y*self.microstepsPerMicrons,
                              z*self.microstepsPerMicrons)
      
      self.moveInMicrostepsTo( positionInMicrosteps)

    def moveBy(self, delta) -> bool:
      """ Move by a delta displacement (dx, dy, dz) from current position in microns """

      dx,dy,dz  = delta
      position = self.position()
      if position is not None:
          x,y,z = position
          self.moveTo( (x+dx, y+dy, z+dz) )

if __name__ == "__main__":
    device = SutterDevice()

    x,y,z = device.position()
    device.moveTo( (x+10, y+10, z+10) )
    device.moveBy( (-10, -10, -10) )
```

We have made significant progress, but there are still problems or at least areas that can be improved:

1. The code above has not been fully tested.  How do we test this? Is it necessary? The solution will be **Unit Testing**. *Hint*: when we do, we will learn that the **move** command actually sends a 0x00 byte at a regular interval when the move is taking a long time. This is not in the documentation but it sure is in the device. 
2. In fact, the code above was not tested at all, because I don't have the device on my computer, it is only in the lab and I wrote the code from home.  It would be nice to be able to test even without the device connected, especially when we integrate this code into other larger projects. The solution will be a mock (i.e. fake) **DebugSutterDeviceUSBPort** that behaves like the real thing. This will require abstracting away the **USBPort** itself.
3. Error management is not easy with hardware devices. They can fail, they can be disconnected, they can be missing, the firmware in the device can be upgraded, etc... If the command times out, what are you supposed to do? Can you recover? The solution is a more general class **PhysicalDevice** that can manage these aspects, while offering enough flexibility to adapt to any type of device. The is the strategy behind **PyHardwareLibrary**.
4. We are putting a lot of work in this Sutter Instrument stage, but what if it breaks and your supervisor purchases or borrows another device (say a Prior)?  Should you change all your code? It is, after all, just another linear stage. The solution to this is a **LinearMotionDevice** base class that will offer a uniform set of functions to move and get the position, without knowing any details about the device itself. This way, the **SutterDevice** will inherit from **LinearMotionDevice**, and a new **PriorDevice** would also inherit from it and could act as a perfect substitute. This approach, which requires time investment in the short term, will limit the impact of any change in the future.  You can take a look at [**OISpectrometer**](https://github.com/DCC-Lab/PyHardwareLibrary/blob/c6fa50b932945388bb5bfce443669158275c5db4/hardwarelibrary/spectrometers/oceaninsight.py) in the PyHardwareLibrary for an example, where two spectrometers can be used interchangeably since they both derive from OISpectrometer, which can return a **USB2000** or a **USB4000** depending on what is connected.

# References

I have found various web sites over the years that may help you understand better, even though everything I wrote above is from experience accumulated over the years. Many web sites are either too detailed or too superficial. It is hard to find reasonable information, but I like the following:

1. "Beyond Logic", https://www.beyondlogic.org/usbnutshell/usb1.shtml.  Really complete, but may be too difficult.
2. "USB made simple", https://www.usbmadesimple.co.uk/index.html.  In the present document, I completely gloss over the fact that there is an Control endpoint #0 (IN/OUT).  All the "USB details" occur on those endpoints and it is not described in the USB Descriptors because it must be there and is not configurable. This document will give you more information to understand the nitty-gritty details if you are interested. (I myself have never learned these details, this is too low-level for me). This would be useful if you are making a USB chip.
3. "Pourquoi j'aime controler les appareils", https://github.com/dccote/Enseignement/blob/master/DAQ/Semaine-01.md
4. A small demo (in french) for serial communications with the FTDI chip: https://github.com/dccote/Enseignement/blob/master/DAQ/Semaine-02.md

**Post-scriptum**

Interesting: you made it this far.  If you want to discuss the possibility of an intership at some point in my group, send me an email with the subject "productId=stage", and tell me the vendorId of FTDI. Then we can talk.