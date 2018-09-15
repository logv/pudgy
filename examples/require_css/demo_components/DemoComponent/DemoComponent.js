var style = require("./DemoComponent.sass");

console.log("STYLE IS", style);

module.exports = {
  className: style.className,
  events: {
    "click" : "handle_click"
  },
  handle_click: function(where) {
    console.log("I WAS CLICKED!", where);
  }
};
