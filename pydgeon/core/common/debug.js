module.exports = {
  make: function() {
    function debug() {
      if (!debug.DEBUG) {
        return
      }

      console.log(_.toArray(arguments).join(" "));
    }
    debug.DEBUG = false;

    return debug;
  }
};

