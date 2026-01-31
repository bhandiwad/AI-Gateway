const USD_TO_INR = 83.5;

export const formatINR = (amountUSD) => {
  const inrAmount = (amountUSD || 0) * USD_TO_INR;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(inrAmount);
};

export const formatINRCompact = (amountUSD) => {
  const inrAmount = (amountUSD || 0) * USD_TO_INR;
  if (inrAmount >= 10000000) {
    return `₹${(inrAmount / 10000000).toFixed(2)} Cr`;
  } else if (inrAmount >= 100000) {
    return `₹${(inrAmount / 100000).toFixed(2)} L`;
  } else if (inrAmount >= 1000) {
    return `₹${(inrAmount / 1000).toFixed(1)}K`;
  }
  return `₹${inrAmount.toFixed(2)}`;
};

export const convertToINR = (amountUSD) => {
  return (amountUSD || 0) * USD_TO_INR;
};

export { USD_TO_INR };
