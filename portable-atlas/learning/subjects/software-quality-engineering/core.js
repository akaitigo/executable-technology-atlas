function contains(x, lo, hi) {
  const afterStart = x >= lo;
  const beforeEnd = x < hi;
  return afterStart && beforeEnd;
}
if (typeof module !== 'undefined') module.exports = {contains};
