$(document).ready(function() {
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        $('#uploadSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);

        $.ajax({
            url: '/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#summaryPreview').html(response.preview.replace(/\n/g, '<br>'));
                $('#downloadOnePage').attr('href', response.downloads.one_page);
                $('#downloadTwoPage').attr('href', response.downloads.two_page);
                $('#summarySection').removeClass('d-none');
                $('#evalResults').addClass('d-none');
            },
            error: function(xhr) {
                alert('Error processing documents: ' + xhr.responseJSON.error);
            },
            complete: function() {
                $('#uploadSpinner').addClass('d-none');
                $('button[type="submit"]').prop('disabled', false);
            }
        });
    });

    $('#runEvaluation').click(function() {
        $('#evalSpinner').removeClass('d-none');
        $(this).prop('disabled', true);

        $.ajax({
            url: '/evaluate',
            type: 'GET',
            success: function(response) {
                $('#relevancyScore').text((response.relevancy * 100).toFixed(1) + '%');
                $('#faithfulnessScore').text((response.faithfulness * 100).toFixed(1) + '%');
                $('#recallScore').text((response.recall * 100).toFixed(1) + '%');
                $('#evalResults').removeClass('d-none');
            },
            error: function(xhr) {
                alert('Evaluation failed: ' + xhr.responseJSON.error);
            },
            complete: function() {
                $('#evalSpinner').addClass('d-none');
                $('#runEvaluation').prop('disabled', false);
            }
        });
    });
});