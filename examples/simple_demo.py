#!/usr/bin/env python
import sys
sys.path.append("../")
import pssm

import platform
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
    device = "Emulator"
else:
    device = "Kobo"


#Declare the Screen Stack Manager
screen = pssm.ScreenStackManager(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread()
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Create a blank canvas
screen.createCanvas()
print("just made canvas")





def demo1():
    def reactFctn(elt,coords):
        print(coords," - ",elt.text)
        print(elt.area)
        print("")

    button1 = pssm.Button("Hey", onclickInside=reactFctn)
    button2 = pssm.Button("Hey2",onclickInside=reactFctn)
    button3 = pssm.Button("Hey3",onclickInside=reactFctn)
    layout_demo = [
        [30                                                                             ],
        [100, (None,"?/2"), (button1,300), (None,"?/2")                                 ],
        [30                                                                             ],
        [100, (None,20), (button2,200), (None,20)                                       ],
        [30                                                                             ],
        [100, (None,20), (button3,200), (None,20), (pssm.Button("nope"),300), (None,10)  ],
        [40]
    ]
    myLayout = pssm.Layout(layout_demo,screen.area)
    screen.addElt(myLayout)
    print("waiting")
    screen.device.wait(2)
    print("done waiting")
    button1.update(newAttributes={
        'text':"Things can change"
    })



def demo2():
    reactFctn = lambda elt,coords : print(coords," - ",elt.text)
    myButtonList = pssm.ButtonList(
        buttons = [
            {'text':'Yup1','onclickInside':reactFctn},
            {'text':'Yup2','onclickInside':reactFctn},
            {'text':'Yup3','onclickInside':reactFctn},
            {'text':'Yup4','onclickInside':reactFctn},
            {'text':'Yup5','onclickInside':reactFctn}
        ],
        margins = [200,200,100,100],
        spacing = 30,
        area = screen.area
    )
    screen.addElt(myButtonList)



def demo3():
    reactFctn   = lambda elt,coords : print(coords," - ",elt.text)
    buttons     = [{'text':'This is button number : ' + str(n), 'onclickInside':reactFctn} for n in range(8)]
    buttonList  = pssm.ButtonList(buttons=buttons, margins=[30,30,100,100], spacing=10)
    button_welcome  = pssm.Button(text="Welcome !",radius=20, background_color = 220, font=pssm.Merri_bold, font_size = 35)
    button_previous = pssm.Button("Previous",onclickInside = reactFctn)
    button_reboot   = pssm.Button("Reboot")
    button_next     = pssm.Button("Next")
    menu = [
        [30                                                                                                             ],
        [100,            (None,80),                       (button_welcome,"?"),                    (None,80)            ],
        ["?",                                               (buttonList,"?")                                            ],
        [100,(None,30), (button_previous,"?*1"), (None,30), (button_reboot,"?*2"), (None,30), (button_next,"?*1"), (None,30)  ],
        [30                                                                                                             ]
    ]
    myLayout = pssm.Layout(menu,screen.area)
    screen.addElt(myLayout)

demo1()
