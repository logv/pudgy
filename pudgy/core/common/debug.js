module.exports = {
  make: function() {
    function debug() {
      if (!debug.DEBUG) {
        return
      }

      console.log(...arguments);
    }
    debug.DEBUG = false;

    return debug;
  }
};

