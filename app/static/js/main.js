$(document).ready(function() {
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        $('#uploadSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);

        $.ajax({
            url: '/process',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                $('#summaryPreview').html(response.summary);
                $('#downloadFull').attr('href', `/download/${response.filename}`);
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
                $('#relevancyScore').text(response.relevancy.toFixed(2));
                $('#faithfulnessScore').text(response.faithfulness.toFixed(2));
                $('#recallScore').text(response.recall.toFixed(2));
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