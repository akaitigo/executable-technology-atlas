/* Custom button keyboard policy. Native buttons deliberately do not use this. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AccessKeyboard = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function transition(armed, event) {
    if (event.type === 'blur' || event.disabled) return {armed: false, activate: false, prevent: event.key === ' '};
    if (event.type === 'keydown' && event.key === 'Enter') return {armed: false, activate: !event.repeat, prevent: true};
    if (event.type === 'keydown' && event.key === ' ') return {armed: armed || !event.repeat, activate: false, prevent: true};
    if (event.type === 'keyup' && event.key === ' ') return {armed: false, activate: armed && event.focused, prevent: true};
    return {armed, activate: false, prevent: false};
  }
  return {transition};
});
