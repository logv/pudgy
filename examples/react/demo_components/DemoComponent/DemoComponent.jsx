import renderer from "./external_renderer.jsx";

var React = $require("react");

module.exports = React.createClass({
  handle_click: function(where) {
    console.log("I WAS CLICKED!", where);
  },
  render: function() {
    return <div className='outerdiv'>
      { renderer.render.apply(this) }
    </div>
  }
});
