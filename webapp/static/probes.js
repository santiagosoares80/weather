$(document).ready(function(){
	var probedelid;
	var probedesc;
	$(document).on('show.bs.modal', '#probedelModal', function (event) {
  		var button = $(event.relatedTarget)
  		probedelid = button.data('probeid')
		probedesc = button.data('probedesc')
  		var modal = $(this)
  		modal.find('.modal-body').text('You are about to delete probe ' + probedelid + ' (' + probedesc + ') ! All data collected by the probe will also be deleted! Are you sure?')
	});
	$('#confirm-del-probe').on('click', function() {
		$('#probedelModal').modal('hide');
		$('<form action="/probes" method="POST">' +
		  '<input type="hidden" name="probe" value="' + probedelid  + '">' +
		  '</form>').appendTo($(document.body)).submit();
	});
});

