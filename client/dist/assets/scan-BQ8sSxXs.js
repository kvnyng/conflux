import{S as h,P as y,W as f,B as M,a as E,T as g,C as L,F as c,b as T}from"./three.module-DaOiP1Qo.js";const C="http://api.cosmicimprint.org",b=C+"/scan/upload/",l=new h,t=new y(75,window.innerWidth/window.innerHeight,.1,1e3),s=new f({antialias:!0});s.setSize(window.innerWidth,window.innerHeight);document.body.appendChild(s.domElement);window.addEventListener("resize",()=>{t.aspect=window.innerWidth/window.innerHeight,t.updateProjectionMatrix(),s.setSize(window.innerWidth,window.innerHeight)});const d=new M,x=new E({size:2.5,vertexColors:!0,map:new g().load("https://threejs.org/examples/textures/sprites/circle.png"),alphaTest:.5,transparent:!0}),A=5e4,m=[],p=[];for(let n=0;n<A;n++){m.push((Math.random()-.5)*2e3,(Math.random()-.5)*2e3,(Math.random()-.5)*2e3);const e=new L().setHSL(Math.random(),1,.9);p.push(e.r,e.g,e.b)}d.setAttribute("position",new c(m,3));d.setAttribute("color",new c(p,3));const w=new T(d,x);l.add(w);t.position.set(0,0,300);const r={x:0,y:0,z:0},H=5e-4,P=75e-5;function S(){r.x=Math.sin(Date.now()*H)*20,r.y=Math.sin(Date.now()*P)*15,t.position.x=r.x,t.position.y=r.y,t.lookAt(0,0,0)}function u(){requestAnimationFrame(u),w.rotation.y+=5e-4,S(),s.render(l,t)}u();const _=document.getElementById("upload-form"),i=document.getElementById("response");let v=null;_.addEventListener("submit",async n=>{n.preventDefault();const e=new FormData;e.append("name",document.getElementById("name").value),e.append("file",document.getElementById("file").files[0]);try{const o=await fetch(b,{method:"POST",body:e}),a=await o.json();o.ok?(i.innerHTML=`<p style="color: green;">${a.message}</p><p style ="color: white;">Look up! You'll see your imprint on the cosmos shortly.</p>`,v=a.data):i.innerHTML=`<p style="color: red;">Error: ${a.detail}</p>`}catch(o){i.innerHTML=`<p style="color: red;">Error: ${o.message}</p>`}});
