import { motion } from 'framer-motion'

interface LogoProps {
  collapsed?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function Logo({ collapsed = false, size = 'md' }: LogoProps) {
  const sizes = {
    sm: { icon: 32, text: 'text-lg' },
    md: { icon: 40, text: 'text-xl' },
    lg: { icon: 48, text: 'text-2xl' },
  }

  const { icon, text } = sizes[size]

  return (
    <motion.div 
      className="flex items-center gap-3"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div 
        className="rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-green-500 p-2 flex items-center justify-center"
        style={{ width: icon, height: icon }}
      >
        <svg 
          viewBox="0 0 24 24" 
          fill="none" 
          className="w-full h-full"
          stroke="white" 
          strokeWidth="2" 
          strokeLinecap="round"
        >
          <path d="M4 18C4 18 6 12 12 12C18 12 20 18 20 18" />
          <path d="M4 14C4 14 6 8 12 8C18 8 20 14 20 14" />
          <path d="M8 10C8 10 9 6 12 6C15 6 16 10 16 10" />
        </svg>
      </div>
      
      {!collapsed && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.2 }}
        >
          <h1 className={`font-bold ${text} bg-gradient-to-r from-blue-400 via-cyan-400 to-green-400 bg-clip-text text-transparent`}>
            StratGen
          </h1>
          <p className="text-xs text-slate-500">AI Presentation Engine</p>
        </motion.div>
      )}
    </motion.div>
  )
}
