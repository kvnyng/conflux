import{S as h,P as y,W as f,B as M,a as E,T as g,C,F as c,b as L}from"./three.module-DaOiP1Qo.js";const l=new h,t=new y(75,window.innerWidth/window.innerHeight,.1,1e3),s=new f({antialias:!0});s.setSize(window.innerWidth,window.innerHeight);document.body.appendChild(s.domElement);window.addEventListener("resize",()=>{t.aspect=window.innerWidth/window.innerHeight,t.updateProjectionMatrix(),s.setSize(window.innerWidth,window.innerHeight)});const d=new M,b=new E({size:2.5,vertexColors:!0,map:new g().load("https://threejs.org/examples/textures/sprites/circle.png"),alphaTest:.5,transparent:!0}),x=5e4,m=[],p=[];for(let n=0;n<x;n++){m.push((Math.random()-.5)*2e3,(Math.random()-.5)*2e3,(Math.random()-.5)*2e3);const e=new C().setHSL(Math.random(),1,.9);p.push(e.r,e.g,e.b)}d.setAttribute("position",new c(m,3));d.setAttribute("color",new c(p,3));const w=new L(d,b);l.add(w);t.position.set(0,0,300);const r={x:0,y:0,z:0},A=5e-4,T=75e-5;function H(){r.x=Math.sin(Date.now()*A)*20,r.y=Math.sin(Date.now()*T)*15,t.position.x=r.x,t.position.y=r.y,t.lookAt(0,0,0)}function u(){requestAnimationFrame(u),w.rotation.y+=5e-4,H(),s.render(l,t)}u();const v="http://10.250.144.197:8000/scan/upload",B=document.getElementById("upload-form"),i=document.getElementById("response");let P=null;B.addEventListener("submit",async n=>{n.preventDefault();const e=new FormData;e.append("name",document.getElementById("name").value),e.append("file",document.getElementById("file").files[0]);try{const o=await fetch(v,{method:"POST",body:e}),a=await o.json();o.ok?(i.innerHTML=`<p style="color: green;">${a.message}</p><p style ="color: white;">Look up! You'll see your imprint on the cosmos shortly.</p>`,P=a.data):i.innerHTML=`<p style="color: red;">Error: ${a.detail}</p>`}catch(o){i.innerHTML=`<p style="color: red;">Error: ${o.message}</p>`}});
