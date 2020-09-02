$(document).ready(function(){
	var eventdel;
	$(document).on('show.bs.modal', '#eventdelModal', function (event) {
  		var button = $(event.relatedTarget)
  		eventdel = button.data('eventtype')
  		var modal = $(this)
  		modal.find('.modal-body').text('You are about to delete event type ' + eventdel + '! Are you sure?')
	});
	$('#confirm-del-event').on('click', function() {
		$('#eventdelModal').modal('hide');
		$('<form action="/events" method="POST">' +
		  '<input type="hidden" name="eventtype" value="' + eventdel  + '">' +
		  '</form>').appendTo($(document.body)).submit();
	});
});

