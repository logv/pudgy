module.exports = {
  events: {
    "click" : "handle_click"
  },
  handle_click: function(where) {
    console.log("I WAS CLICKED!", where);
  }
};
