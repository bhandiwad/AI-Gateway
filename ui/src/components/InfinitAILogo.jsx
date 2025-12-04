export default function InfinitAILogo({ className = "w-8 h-8" }) {
  return (
    <svg className={className} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path 
        d="M20 5C12 5 8 12 8 20C8 28 12 35 20 35C28 35 32 28 32 20" 
        stroke="#84cc16" 
        strokeWidth="4" 
        strokeLinecap="round"
        fill="none"
      />
      <path 
        d="M20 35C28 35 32 28 32 20C32 12 28 5 20 5" 
        stroke="#22c55e" 
        strokeWidth="4" 
        strokeLinecap="round"
        fill="none"
      />
      <circle cx="20" cy="20" r="3" fill="#84cc16" />
    </svg>
  );
}
