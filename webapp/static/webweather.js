$(document).ready(function(){
	var capdel;
	$(document).on('show.bs.modal', '#capdelModal', function (event) {
  		var button = $(event.relatedTarget) // Button that triggered the modal
  		capdel = button.data('cap') // Extract info from data-* attributes
  		// If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
  		// Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
  		var modal = $(this)
  		modal.find('.modal-body').text('You are about to delete capability ' + capdel + '! Are you sure?')
	});
	$('#confirm-del-cap').on('click', function() {
		$('#capdelModal').modal('hide');
		$('<form action="/capabilities" method="POST">' +
		  '<input type="hidden" name="capability" value="' + capdel  + '">' +
		  '</form>').appendTo($(document.body)).submit();
	});
});

