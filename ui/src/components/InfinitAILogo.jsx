import logoImage from '@assets/image_1764856519093.png';

export default function InfinitAILogo({ className = "w-8 h-8" }) {
  return (
    <img 
      src={logoImage} 
      alt="InfinitAI Logo" 
      className={className}
    />
  );
}
