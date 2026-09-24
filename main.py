from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

app = FastAPI()
users = {}
msgs = []

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChatWave - Real Time</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:Arial}
body{background:#0e1621;color:#fff;height:100vh;display:flex;flex-direction:column}
.top{background:#17212b;padding:12px 15px;display:flex;justify-content:space-between;border-bottom:1px solid #2b5278}
.logo{color:#5288c1;font-weight:bold;font-size:18px}
.chat{flex:1;overflow-y:auto;padding:15px;display:flex;flex-direction:column;gap:8px}
.m{max-width:75%;padding:8px 12px;border-radius:10px;font-size:14px;word-wrap:break-word}
.me{align-self:flex-end;background:#2b5278}
.you{align-self:flex-start;background:#182533}
.input{padding:10px;background:#17212b;display:flex;gap:8px}
.input input{flex:1;padding:12px;border-radius:20px;border:none;background:#242f3d;color:#fff;outline:none}
.input button{width:45px;height:45px;border-radius:50%;border:none;background:#5288c1;color:#fff;font-size:18px}
.login{position:fixed;inset:0;background:#0e1621;display:flex;align-items:center;justify-content:center;z-index:100}
.box{background:#17212b;padding:25px;border-radius:12px;width:90%;max-width:320px;text-align:center}
.box h2{color:#5288c1}
.box input{width:100%;padding:12px;margin:15px 0;border-radius:8px;border:none;background:#242f3d;color:#fff}
.box button{width:100%;padding:12px;background:#5288c1;border:none;border-radius:8px;color:#fff;font-weight:bold}
.online{font-size:11px;color:#7d8b99;padding:5px 15px;background:#17212b}
.time{font-size:9px;opacity:.5;margin-top:4px;text-align:right}
</style>
</head>
<body>
<div class="login" id="L"><div class="box"><h2>CHATWAVE</h2><p style="font-size:12px;color:#7d8b99;margin-top:5px">Fast Real-Time Chat</p><input id="U" placeholder="Enter your name"><button onclick="join()">JOIN NOW</button></div></div>
<div class="top"><div><div class="logo">ChatWave</div><div style="font-size:11px;color:#7d8b99" id="C">0 online</div></div><div id="N" style="font-size:13px;color:#5288c1"></div></div>
<div class="online" id="UL"></div>
<div class="chat" id="M"></div>
<div class="input"><input id="T" placeholder="Message..." onkeypress="if(event.key=='Enter')send()"><button onclick="send()">➤</button></div>
<script>
let ws, myName;
function join(){
  myName=document.getElementById('U').value.trim();
  if(!myName)return alert('Enter name');
  document.getElementById('L').style.display='none';
  document.getElementById('N').innerText='@'+myName;
  let proto=location.protocol=='https:'?'wss://':'ws://';
  ws=new WebSocket(proto+location.host+'/ws/'+myName);
  ws.onmessage=(e)=>{
    let d=JSON.parse(e.data);
    if(d.type=='init'){
      document.getElementById('C').innerText=d.users.length+' online';
      document.getElementById('UL').innerText=d.users.join(', ');
      d.msgs.forEach(x=>show(x));
    }else if(d.type=='msg'){
      show(d);
    }else if(d.type=='users'){
      document.getElementById('C').innerText=d.users.length+' online';
      document.getElementById('UL').innerText=d.users.join(', ');
    }
  };
}
function show(m){
  let div=document.createElement('div');
  div.className='m '+(m.sender==myName?'me':'you');
  div.innerHTML=(m.sender!=myName?'<b style="color:#5288c1;font-size:11px">'+m.sender+'</b><br>':'')+m.text+'<div class="time">'+m.time+'</div>';
  document.getElementById('M').appendChild(div);
  document.getElementById('M').scrollTop=999999;
}
function send(){
  let inp=document.getElementById('T');
  if(!inp.value.trim()||!ws)return;
  ws.send(JSON.stringify({text:inp.value}));
  inp.value='';
}
</script>
</body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(HTML)

@app.websocket("/ws/{name}")
async def websocket_endpoint(websocket: WebSocket, name: str):
    await websocket.accept()
    users[name] = websocket

    # send history + users
    await websocket.send_text(json.dumps({"type":"init","users":list(users.keys()),"msgs":msgs[-50:]}))

    # tell others
    for u, s in users.items():
        if u!= name:
            try: await s.send_text(json.dumps({"type":"users","users":list(users.keys())}))
            except: pass

    try:
        while True:
            data = await websocket.receive_text()
            j = json.loads(data)
            m = {"type":"msg","sender":name,"text":j.get("text","")[:500],"time":datetime.now().strftime("%H:%M")}
            msgs.append(m)
            if len(msgs) > 200: msgs.pop(0)
            for s in users.values():
                try: await s.send_text(json.dumps(m))
                except: pass
    except WebSocketDisconnect:
        if name in users: del users[name]
        for s in users.values():
            try: await s.send_text(json.dumps({"type":"users","users":list(users.keys())}))
            except: pass
