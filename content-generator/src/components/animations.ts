export const useEntrance = (delay = 0) => {
  void delay;
  return {
    opacity: 1,
    transform: "translateY(0px)"
  };
};

export const revealValue = (value: number, delay = 0) => {
  void delay;
  return value;
};
