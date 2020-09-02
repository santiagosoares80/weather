$(document).ready(function(){
	var userid;
	$(document).on('show.bs.modal', '#userdelModal', function (event) {
		var button = $(event.relatedTarget) 
		userid = button.data('userid')
		username = button.data('username')
		var modal = $(this)
		modal.find('.modal-body').text('You are about to delete user ' + username + '! Are you sure?')
	});
	$('#confirm-del-user').on('click', function() {
		$('#userdelModal').modal('hide');
		$('<form action="/users" method="POST">' +
		  '<input type="hidden" name="userid" value="' + userid + '">' +
		  '</form>').appendTo($(document.body)).submit();
	});
});

