module.exports = {
  initialize: function(ctx) {
    console.log("LOADED DEMO PAGE", ctx);
  },
  SetComponent: function fn(cmp) {
    console.log("SETTING COMPONENT", cmp);

//    this.bridge.server_call("FOOBAR");
  }
};
