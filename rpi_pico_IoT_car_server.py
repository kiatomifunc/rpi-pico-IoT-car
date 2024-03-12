import network
import time
import socket
from machine import Pin, Timer, PWM

def web_page():
    html = """<html>
   <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style type="text/css">
	a {
	  position:fixed;
	  background-color: #006688;
	  color: FFFFFF;
	  padding: 50px;
	  border-radius: 50px;
	  -moz-border-radius: 10px;
	  -webkit-border-radius: 10px;
	  transform: translate(-50%, -50%);
	  font-size:20px;
	  }
	  </style>
   </head>
   <body>
     <script>
       function sending(data1,data2)
       {
	 var xhr = new XMLHttpRequest();
	 xhr.open("POST", "/", true);
	 xhr.setRequestHeader('Content-Type',
	 data1.toString()+','+data2.toString());
	 xhr.send(JSON.stringify({value1: data1,value2: data2}));
       }
		
       window.onload=function()
       {
	 document.addEventListener("touchstart",(e)=> {
	   var x = e.touches[0].clientX/window.innerWidth;
	   x = 0.5-x.toPrecision(4)
	   x = 2*x
	   var y = e.touches[0].clientY/window.innerHeight;
	   y = 0.5-y.toPrecision(4)
	   y = 2*y
	   sending(x,y);
	   })
	   
	 document.addEventListener("touchend",(e)=> {
	   sending(0,0);
	   });
	 
	 document.addEventListener("touchcancel",(e)=> {
	   sending(0,0);
	   });
	 }
		
	</script>
	<a style="top:10%; left:50%">forward</a>
	<a style="top:50%; left:10%">left</a>
	<a style="top:50%; left:90%">right</a>
	<a style="top:90%; left:50%">backward</a>
   </body>
</html>

         """
    return html

led = Pin("LED", Pin.OUT)
tim = Timer()
def tick(timer):
    global led
    led.toggle()

def ledindicator(active):
    if active:
        tim.deinit()
        led.value(1)
    else:
        tim.init(freq=4, mode=Timer.PERIODIC, callback=tick)

#for back ward 
forpin = Pin(0, Pin.OUT)
backpin = Pin(1, Pin.OUT)
leftpin = Pin(2, Pin.OUT)
rightpin = Pin(3, Pin.OUT)
#for back ward speed control
fbspeedpin = PWM(Pin(4))
fbspeedpin.freq(1000)
fbspeedpin.duty_u16(0)
#left right speed control
rlspeedpin = machine.ADC(26)
#global angle variable
angle = 0

def speedsensor(set_angle):
    global angle
    prev = False
    
    while angle!=set_angle:
        
        if angle<set_angle:
            leftpin.value(1)
            rightpin.value(0)
        elif angle>set_angle:
            leftpin.value(0)
            rightpin.value(1)
        #current pin values
        var = rlspeedpin.read_u16()
        #calc if turns left or right
        #print(var)
        if var>6000 and (not prev) and angle<set_angle:
            angle += 1
            #print(f"angle: {angle}")
            prev = True
        elif var>6000 and (not prev) and angle>set_angle:
            angle -= 1
            #print(f"angle: {angle}")
            prev = True
        elif var<=6000:
            prev = False
        
        #previuse values
        time.sleep(0.001)


def rlcontrol(percent):
    angle_const = 5*8
    
        
    angle = speedsensor(int(angle_const*percent))
    leftpin.value(0)
    rightpin.value(0)
    


def fbspeed(percent):
    fbspeedpin.duty_u16(int(abs(percent)/2*65535))

def driveforward(percent):
    fbspeed(percent)
    if percent<0:
        forpin.value(1)
        backpin.value(0)
    elif percent>0:
        forpin.value(0)
        backpin.value(1)
    else:
        forpin.value(0)
        backpin.value(0)


    



# if you do not see the network you may have to power cycle
# unplug your pico w for 10 seconds and plug it in again
def ap_mode(ssid, password):
    """
        ssid[str]: The name of your internet connection
        password[str]: Password for your internet connection

    """
    # Just making our internet connection
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    while ap.active() == False:
        pass
    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + ap.ifconfig()[0])
    ledindicator(0)
    

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
    s.bind(('', 8080))
    s.listen(5)

    header = 'HTTP/1.0 200 OK\nContent-Type: text/html\n\n'
    response = header+web_page()
    while True:
        conn, addr = s.accept()
        #print('Got a connection from %s' % str(addr))
        ledindicator(1)
        request = conn.recv(1024)
        request = str(request)
        #print('Content = %s' % request)
      
      
        if request[2:5]=="GET":
            #response = header+web_page()
            conn.send(response.encode())
        elif request[2:6]=="POST":
            #response = header
            
            lines = request.split("\\r\\n")
            data = lines[2]
            data = data[14:]
            
            rl,fb = data.split(',')
            rl,fb = float(rl),float(fb)
            #print(rl,fb)
            
            if rl==0 and fb==0:
                driveforward(fb)
            else:
                rlcontrol(rl)
                driveforward(fb)

        #conn.send(response.encode())
        conn.close()
ap_mode('ssid',
        'password')










