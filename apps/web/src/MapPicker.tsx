import {useEffect,useRef,useState} from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
const downtown: L.LatLngTuple = [29.6516, -82.3248]
export default function MapPicker({latitude,longitude,onSelect}:{latitude:number|null;longitude:number|null;onSelect:(lat:number,lon:number)=>void}){
 const ref=useRef<HTMLDivElement>(null), map=useRef<L.Map|null>(null), marker=useRef<L.CircleMarker|null>(null),handler=useRef(onSelect)
 const [tilesFailed,setTilesFailed]=useState(false)
 handler.current=onSelect
 useEffect(()=>{if(!ref.current)return;const instance=L.map(ref.current,{scrollWheelZoom:false}).setView(latitude===null||longitude===null?downtown:[latitude,longitude],13);map.current=instance
 const tile=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(instance)
 tile.on('tileerror',()=>setTilesFailed(true))
 instance.on('click',(e:L.LeafletMouseEvent)=>handler.current(e.latlng.lat,e.latlng.lng))
 const abort=new AbortController();fetch('/api/v1/boundary',{signal:abort.signal}).then(r=>r.ok?r.json():null).then(g=>{if(g)L.geoJSON(g,{style:{color:'#246851',weight:2,fillOpacity:.05}}).addTo(instance)}).catch(()=>{})
 return()=>{abort.abort();instance.remove();map.current=null;marker.current=null}
 },[])
 useEffect(()=>{
  if(!map.current)return
  if(latitude===null||longitude===null){marker.current?.remove();marker.current=null;return}
  const position:L.LatLngTuple=[latitude,longitude]
  if(marker.current)marker.current.setLatLng(position)
  else marker.current=L.circleMarker(position,{radius:9,color:'#fff',weight:3,fillColor:'#c45b2e',fillOpacity:1}).addTo(map.current)
  if(!map.current.getBounds().contains(position))map.current.panTo(position)
 },[latitude,longitude])
 return <><div className="map" ref={ref} aria-label="Gainesville location map; use coordinate fields below as a keyboard alternative"/>{tilesFailed&&<p className="hint">Map tiles are unavailable. You can still enter coordinates and confirm your location below.</p>}<p className="map-note">Tap the map to place a pin. City boundary shown in green. Map tiles use OpenStreetMap; report photos and text stay local.</p></>
}
