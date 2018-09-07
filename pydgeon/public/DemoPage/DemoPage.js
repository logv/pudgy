module.exports = {
  initialize: function(ctx) {
    console.log("LOADED DEMO PAGE", ctx);
  },
  SetComponent: function(cmp) {
    this.rpc
      .server_call()
      .kwargs({ component: cmp })
      .done(function(res, error) {
        if (error) {
          console.log("ERR", error);
          return
        }

        console.log("server_call SUCCESS", res);
      });
  },
  handle_data: function fn() {
    console.log("SERVER INVOKED RPC", fn.__kwargs__, fn.__args__);
  }
};
