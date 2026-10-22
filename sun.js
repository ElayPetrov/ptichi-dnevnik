// Изгрев, залез и гражданска зора/здрач (Слънцето 6° под хоризонта) по уравнението на изгрева.
// Връща минути от местната полунощ (часовата зона на устройството); точност около минута.
function sunTimes(d,lat,lon){
  const rad=Math.PI/180,[Y,M,D]=d.split('-').map(Number);
  const n=Math.round(Date.UTC(Y,M-1,D,12)/864e5+2440587.5-2451545+0.0008), Js=n-lon/360;
  const Mr=((357.5291+0.98560028*Js)%360)*rad;
  const C=1.9148*Math.sin(Mr)+0.02*Math.sin(2*Mr)+0.0003*Math.sin(3*Mr);
  const L=((Mr/rad+C+180+102.9372)%360)*rad;
  const Jt=2451545+Js+0.0053*Math.sin(Mr)-0.0069*Math.sin(2*L);       // слънчев обяд
  const dec=Math.asin(Math.sin(L)*Math.sin(23.4397*rad));
  const half=h=>{const c=(Math.sin(h*rad)-Math.sin(lat*rad)*Math.sin(dec))/(Math.cos(lat*rad)*Math.cos(dec));return Math.abs(c)>1?null:Math.acos(c)/rad/360;};
  const loc=j=>{const t=new Date((j-2440587.5)*864e5);return t.getHours()*60+t.getMinutes()+t.getSeconds()/60;};
  const a=half(-0.833), b=half(-6);
  return {noon:loc(Jt),rise:a==null?null:loc(Jt-a),set:a==null?null:loc(Jt+a),dawn:b==null?null:loc(Jt-b),dusk:b==null?null:loc(Jt+b)};
}
module.exports={sunTimes};
