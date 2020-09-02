$(document).ready(function(){
	$('#prbimg').on('change',function(){
		var fileName = $(this).get(0).files.item(0).name;
		$(this).next('.custom-file-label').html(fileName);
	});
});

