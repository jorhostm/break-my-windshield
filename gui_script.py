# -*- coding: utf-8 -*-
"""
Created on Thu Jun 30 09:25:43 2022

@author: knutskl
"""
import numpy as np
from pims import*
import PIL 
from tkinter import *
from PIL import Image, ImageTk
from tkinter import simpledialog
from tkinter import filedialog
from scipy.interpolate import LinearNDInterpolator, CloughTocher2DInterpolator, RegularGridInterpolator

import matplotlib.pyplot as plt
import pandas as pd


#from functions import*
# GUI LOOP
#
# Create an instance of tkinter frame or window
win=Tk()
# Read the .cine file from directory
filename = filedialog.askopenfilename(filetypes=[('Cine','.cine')])
video = Cine(filename)

# i keeps tabs on which frame we are at
i = 0

brg = 25

image = PIL.Image.fromarray(video[i]/256*brg) # make frame into an Image object
w = image.size[0] # width of image
h = image.size[1] # heigth of image

global text # ?

# Set the size of the window
win.geometry("{}x{}".format(1500,1200))

# Create a canvas widget
canvas=Canvas(win, width=w, height=h)
canvas.grid(row = 1, column = 0)

# Output textbox
text = Text()
text.grid(row=1,column=1,sticky='NWSE')

# Frame to keep buttons in
buttons = Frame()
buttons.grid(row=0,column=0,columnspan=2,sticky='NWSE')

# Load the image
img=ImageTk.PhotoImage(image = image) 

# Add the image in the canvas
img_cont = canvas.create_image(w/2,h/2, image=img)

# Textbox which displays Frame number
fps = canvas.create_text((0,0),fill='white', text=f'Frame: {i+1}',anchor='nw')
# Calibration lists
points = [] # pixel values of clicked points
values=[] # Real positional values
boxs = [] # List to contain the point markers

# Dictionary with file results
results = {'Calibration':'X,Y' ,'Interpolation':'Frame,X,Y'}

state = 1 #  1 = calib, 2 = interpol. Starts program in calibration state


inter_data = [] # Real interpolation points
dist = [] # List to contain drawn lines between interpolated points
ipoints = [] # pixel coordinates of interpolated points

total_length = 0 # Total length of crack
time = 0
velocity = 0
nframes = 0
# Label with error info
error = Label(text='Error')
error.grid(row=2,column=1,sticky='w')

# Calculatation results label
calculations = Label(text=f'Total length of crack:'
                     ' {total_length}\nTime:\nVelocity')
calculations.grid(row=2,column=0,sticky='w')

# Frame control using arrow keys
def arrow(event):
    global i, img, canvas, img_cont, fps

    if event.keysym=='Right':
        i +=1
    elif event.keysym=='Left': 
        i -=1
    elif event.keysym=='Up':
        i +=20
    elif event.keysym=='Down':
        i -=20
    if i> len(video)-1: # Stop at last frame
        i = len(video)-1
    elif i<0: # Stop at first frame
        i=0
    # Retrieve next frame
    frame = PIL.Image.fromarray(video[i]/256*brg)
    #Load frame
    img=ImageTk.PhotoImage(image = frame )
    # Display in canvas
    canvas.itemconfig(img_cont,image=img)
    canvas.itemconfig(fps, text=f'Frame: {i+1}')

def draw_lines():
    global canvas, state, text, inter_data, dist, ipoints, total_length, time, velocity, calculations
    for l in dist:
        canvas.delete(l)
    dist.clear()
    if state != 2:
        return
    
    text.config(state=NORMAL)
    text.delete('1.0',END)
    text.insert(END, "Frame\tPoint_X\tPoint_Y\tValue_X\tValue_Y\n")
    for p in zip(ipoints,inter_data):
        ((pointx,pointy),(frame,valuex,valuey)) = p
        text.insert(END, f"{frame}\t{pointx:.1f}\t{pointy:.1f}\t{valuex:.1f}\t{valuey:.1f}\n")
    text.config(state=DISABLED)

    total_length = 0.0
    time = 0.0
    velocity = 0.0
    if len(inter_data) >= 2:
        
        for k in range(len(ipoints)-1):
            (x0,y0),(x1,y1) = ipoints[k], ipoints[k+1]
            dist.append(canvas.create_line((x0,y0),(x1,y1),fill='magenta'))
            
            (f0,x0,y0),(f1,x1,y1) = inter_data[k], inter_data[k+1]
            time += (f1-f0)*(1./25000)
            total_length += np.hypot((x1-x0),(y1-y0))
        
        if time > 0:
            velocity = total_length / time / 1000
        
        
    calculations.config(text=f'Total length of crack:'
                            f' {total_length}\nTime:{time}\n'
                            f'Velocity:{velocity:.0f}')

        
        

def draw_boxes():
    global points, values, text, boxs, canvas, state

    for b in boxs:
        canvas.delete(b)
    boxs.clear()

    for p in points:
        # Create a red square marker 
        lastx,lasty = p
        boxs.append(canvas.create_rectangle((lastx-3
                    ,lasty-3),(lastx+3,lasty+3),fill='red'))
    if state == 1:
        text.config(state=NORMAL)
        text.delete('1.0',END)
        text.insert(END, "Point_X\tPoint_Y\tValue_X\tValue_Y\n")
        for p in zip(points,values):
            ((pointx,pointy),(valuex,valuey)) = p
            text.insert(END, f"{pointx:.1f}\t{pointy:.1f}\t{valuex:.1f}\t{valuey:.1f}\n")
        text.config(state=DISABLED)
        draw_lines()


def write_points():
    global points, values, filename
    pointx = []
    pointy = []
    valuex = []
    valuey = []
    for p in points:
        pointx.append(p[0])
        pointy.append(p[1])
    for v in values:
        valuex.append(v[0])
        valuey.append(v[1])
    df = pd.DataFrame({"pointx":pointx,"pointy":pointy,"valuex":valuex,"valuey":valuey})
    df.to_csv(os.path.splitext(filename)[0] + ".csv",index=False)

def read_points():
    global points, values, filename
    points.clear()
    values.clear()
    file = os.path.splitext(filename)[0]+".csv"
    try:
        df = pd.read_csv(file)
        points = list(zip(df.loc[:,"pointx"],df.loc[:,"pointy"]))
        values = list(zip(df.loc[:,"valuex"],df.loc[:,"valuey"]))

    except:
        pass
    draw_boxes()

def delete_points(event):
    global points, values,state
    if state != 1:
        return
    x, y = event.x, event.y # Get x and y from click
    for i,(px,py) in enumerate(points):
        if np.hypot(x-px,y-py) < 10:
            points.pop(i)
            values.pop(i)
            draw_boxes()
            return

def save_posn(event):
    global points, values
  
    lastx, lasty = event.x, event.y # Get x and y from click
    x = simpledialog.askfloat('x', 'X-coordinate') #Input
    y = simpledialog.askfloat('y', 'Y-coordinate')
    value = (x,y)
    point = (lastx, lasty)
    if any(val == None for val in value) : # Avoids taking invalids into list
        error.config(text='Error:\nInvalid values')
        return
    error.config(text='') # Reset error if all is well
    
    # Save pixel and value data
    points.append(point)
    values.append(value)
    
    
    """
    # Create a red square marker 
    boxs.append(canvas.create_rectangle((lastx-3
                ,lasty-3),(lastx+3,lasty+3),fill='red'))
    """
    draw_boxes()


 
    
def calibration():
    global canvas, state

    if state ==1: # If already in calibration mode, do nothing
        return
    state = 1
    # Replace outputfield
    canvas.bind('<Button-1>',save_posn)
    draw_boxes()

def extrapolate():
    global interpol, points, values, w, h, filename, canvas
    interpolinv = LinearNDInterpolator(values,points)
        
    ls = []
    xcoords = set()
    ycoords = set()
    for v in values:
        xcoords.add(v[0])
        ycoords.add(v[1])
    xcoords = list(xcoords)
    ycoords = list(ycoords)
    xcoords.sort()
    ycoords.sort()
    for x in xcoords:
        lss = []
        for y in ycoords:
            lss.append(interpolinv([x,y])[0])
        ls.append(lss)
    
    interpolinv = RegularGridInterpolator([np.sort(xcoords),np.sort(ycoords)],ls,bounds_error=False,fill_value=None)
    
    
    dx = xcoords[1]-xcoords[0]
    dy = ycoords[1]-ycoords[0]
    xcoords.insert(0,xcoords[0]-dx)
    xcoords.append(xcoords[-1]+dx)
    ycoords.insert(0,ycoords[0]-dy)
    ycoords.append(ycoords[-1]+dy)
    xarr = np.linspace(xcoords[0],xcoords[-1],1000)
    yarr = np.linspace(ycoords[0],ycoords[-1],1000)
    

    for x in xcoords:
        for y in ycoords:
            if (x,y) not in values:
                lastx, lasty = interpolinv((x,y))
                value = (x,y)
                point = (lastx, lasty)
                if any(val == None for val in value) : # Avoids taking invalids into list
                    error.config(text='Error:\nInvalid values')
                    return
                error.config(text='') # Reset error if all is well
                
                # Save pixel and value data
                if not np.isnan(lastx)and not np.isnan(lasty):
                    points.append(point)
                    values.append(value)

    interpolinv = CloughTocher2DInterpolator(values,points)
    for x in xcoords:
        arr = np.array([yarr,yarr])
        arr[0,:] = x
        dat = interpolinv(arr.T)
        plt.plot(dat.T[0],dat.T[1],"k-")
    
    for y in ycoords:
        arr = np.array([xarr,xarr])
        arr[1,:] = y
        dat = interpolinv(arr.T)
        plt.plot(dat.T[0],dat.T[1],"k-")
    
    plt.xlim((0,w))
    plt.ylim((0,h))
    plt.gca().invert_yaxis()
    dpi = win.winfo_fpixels("1i")
    plt.gcf().set_size_inches(w/dpi, h/dpi)
    plt.tight_layout()
    plt.axis('off')
  
    plt.show()

    draw_boxes()

    interpol = CloughTocher2DInterpolator(points,values)


def interpolation():
    global interpol, canvas, points, state, values, results

    if state == 2:
        return
    try:
        # Try to create an interpolator
        #interpol = LinearNDInterpolator(points,values)
        interpolinv = CloughTocher2DInterpolator(values,points)
        xcoords = set()
        ycoords = set()
        for v in values:
            xcoords.add(v[0])
            ycoords.add(v[1])

        for x in xcoords:
            for y in ycoords:
                if (x,y) not in values:
                    lastx, lasty = interpolinv((x,y))
                    value = (x,y)
                    point = (lastx, lasty)
                    if any(val == None for val in value) : # Avoids taking invalids into list
                        error.config(text='Error:\nInvalid values')
                        return
                    error.config(text='') # Reset error if all is well
                    
                    # Save pixel and value data
                    if not np.isnan(lastx)and not np.isnan(lasty):
                        points.append(point)
                        values.append(value)
                    

                    interpolinv = CloughTocher2DInterpolator(values,points)
        
        
        
        draw_boxes()
        
        plt.show()

        state = 2
        error.config(text='')
        
        canvas.bind('<Button-1>',get_pos)
        interpol = CloughTocher2DInterpolator(points,values)
        draw_lines()
    except:
        error.config(text='Error\nNot enough points to construct interpolator')
        
    
def get_pos(event):
    global points, values, interpol, inter_data, i, ipoints
    
    x,y = interpol((event.x,event.y))
    if any(np.isnan((x,y))):
        error.config(text='Error\nPoint out of bounds')
        return
    error.config(text='')
    ipoints.append((event.x,event.y))

    inter_data.append((i+1,x,y)) # frame = i +1, x pos, y pos
    
    draw_lines()
    
def pos_pop(event):
    global points, values, canvas, state, inter_data, total_length, time, velocity, calculations
    
    if state == 1:
        line = len(points)
        points.pop()
        values.pop()
        draw_boxes()
    elif state == 2:
        line = len(inter_data)
        if line >0:
            if line>1:
                xi0, yi0 =inter_data[-2][1],inter_data[-2][2]
                xi1, yi1 =inter_data[-1][1],inter_data[-1][2]
                total_length -= np.hypot(xi1 - xi0,  yi1 - yi0)
                
                time -= (inter_data[-1][0]-inter_data[-2][0])/25000
                if time >0:
                    velocity = total_length/time
                elif time<=0:
                    velocity = 0.0
                    
                calculations.config(text=f'Total length of crack:'
                                    f' {total_length}\nTime:{time}\n'
                                    f'Velocity:{velocity}')
            elif line <= 1:
                total_length = 0.0
                time = 0.0
                velocity = 0.0
                calculations.config(text=f'Total length of crack:'
                                    f' {total_length}\nTime:{time}\n'
                                    f'Velocity:{velocity}')
            inter_data.pop()
            ipoints.pop()
            draw_lines()
        
def file_save():
    global filename, inter_data, ipoints

    write_points()
    
    f = filedialog.asksaveasfile(mode='w', defaultextension=".csv", filetypes=[('CSV','.csv')])
    frames = list()
    pointx = list()
    pointy = list()
    valuex = list()
    valuey = list()
    for (px,py),(frame,vx,vy) in zip(ipoints,inter_data):
        pointx.append(px)
        pointy.append(py)
        frames.append(frame)
        valuex.append(vx)
        valuey.append(vy)
 
    df = pd.DataFrame({"Frame":frames,"pointx":pointx,"pointy":pointy,"X":valuex,"Y":valuey})
    df.to_csv(f.name,index=False)

def brightness(event):
    global brg, i, img, canvas, img_cont, fps

    if event.keysym== '1':
        brg -=1
    elif event.keysym == '2':
        brg+=1
    frame = PIL.Image.fromarray(video[i]/256*brg)
    #Load frame
    img=ImageTk.PhotoImage(image = frame )
    # Display in canvas
    canvas.itemconfig(img_cont,image=img)
    canvas.itemconfig(fps, text=f'Frame: {i+1}')

def open_file():
    global filename, video, i, image, brg, w, h, img, canvas, img_cont, fps

    write_points()
    filename = filedialog.askopenfilename(filetypes=[('Cine','.cine')])
    video = Cine(filename)

    # i keeps tabs on which frame we are at
    i = 0

    image = PIL.Image.fromarray(video[i]/256*brg) # make frame into an Image object
    w = image.size[0] # width of image
    h = image.size[1] # heigth of image
   
    # Load the image
    img=ImageTk.PhotoImage(image = image) 
    canvas.itemconfig(img_cont,image=img)
    canvas.itemconfig(fps, text=f'Frame: {i+1}')
    read_points()
    draw_boxes()
    
    
    
newfile = Button(master=buttons,text='Open new file',command=open_file)      
newfile.grid(row=0,column=4)
save = Button(master=buttons,text='Save file',command=file_save)     
save.grid(row=0,column=3)


calib = Button(master=buttons,text='Calibrate',
               command = calibration)
calib.grid(row =0,column=0,sticky='W')

extrapolate = Button(master=buttons, text='Extrapolate',
                     command= extrapolate)
extrapolate.grid(row=0,column=1)

interpolate = Button(master=buttons, text='Interpolate',
                     command= interpolation)
interpolate.grid(row=0,column=2)


canvas.bind('<Button-1>',save_posn)   
win.bind('<Key-Right>',arrow, add=True)
win.bind('<Key-Left>',arrow, add=True)
win.bind('<Key-Up>',arrow, add=True)
win.bind('<Key-Down>',arrow, add=True)
win.bind('<BackSpace>',pos_pop)
win.bind('<Key-1>',brightness)
win.bind('<Key-2>',brightness,add=True)
win.focus_force()
canvas.bind('<Shift-Button-3>',delete_points) 

read_points()
draw_boxes()
win.mainloop()
