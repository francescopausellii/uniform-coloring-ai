const featuresFunctions = {};

featuresFunctions.getPathCount = (paths) => {
  return paths.length;
};

featuresFunctions.getPointCount = (paths) => {
  const points = paths.flat();
  return points.length;
};

featuresFunctions.getWidth = (paths) => {
  const points = paths.flat();
  const x = points.map((p) => p[0]);
  const min = Math.min(...x);
  const max = Math.max(...x);
  return max - min;
};

featuresFunctions.getHeight = (paths) => {
  const points = paths.flat();
  const y = points.map((p) => p[1]);
  const min = Math.min(...y);
  const max = Math.max(...y);
  return max - min;
};

featuresFunctions.getContour = (paths) => {
  
};

featuresFunctions.inUse = [
  { name: "Path Count", function: featuresFunctions.getPathCount },
  { name: "Point Count", function: featuresFunctions.getPointCount },
  //{ name: "Width", function: featuresFunctions.getWidth },
  //{ name: "Height", function: featuresFunctions.getHeight },
];

if (typeof module !== "undefined") {
  module.exports = featuresFunctions;
}
