$(document).ready(function(){
	var capdel;
	$(document).on('show.bs.modal', '#capdelModal', function (event) {
  		var button = $(event.relatedTarget)
  		capdel = button.data('cap')
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

