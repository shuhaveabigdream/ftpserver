import usb
import array
dev=usb.core.find(idVendor=1155,idProduct=22320)
if dev._kernel_driver_active(0):
    dev.detach_kernel_driver(0)
ep = dev[0][(0,0)][1].bEndpointAddress
my_data = array.array('B',sendlist)
dev.write(ep, my_data)

print(dev)