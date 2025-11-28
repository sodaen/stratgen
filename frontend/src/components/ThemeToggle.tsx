import React from "react";
export function ThemeToggle(){
  const [t,setT] = React.useState<string>(()=>localStorage.getItem("theme")||"dark");
  React.useEffect(()=>{ document.documentElement.setAttribute("data-theme", t); localStorage.setItem("theme", t); },[t]);
  return (
    <button className="btn" onClick={()=>setT(t==="dark"?"light":"dark")} title="Theme umschalten">
      {t==="dark" ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}
