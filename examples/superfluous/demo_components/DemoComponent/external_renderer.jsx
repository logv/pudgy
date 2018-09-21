module.exports = {
  render: function() {
    return <div>
      <h1>{ this.props.title }</h1>

      { this.props.about }
    </div>


  }
}
