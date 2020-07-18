// Run from console on https://www.youtube.com/c/lockpickinglawyer/videos or analagous
ids = [...document.querySelectorAll("#primary #video-title[href]")]
 .map(e=>/\?v=(.*)/.exec(e.href)[1])
 .map(e=>e.slice(0,11))
console.log(`["${ids.join('", "')}"]`)
