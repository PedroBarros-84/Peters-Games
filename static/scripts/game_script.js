$(document).ready(function(){

    /* Set global variables for Countdown Timer function */
    var miliseconds = 60000;
    var timer = null;
    var countDownStarted = false;

    /* Set global variables for Card Flipper Function */
    var clickCount = 0;
    var pairCount = 0;
    var card1originalID = 0;
    var clickEnabled = true;
    var user_points = Number($('#points').text());

    /* Countdown Timer function and final points calculation */
    function countDown() {

        /* Decrease one second every repetition */
        miliseconds -= 1000;

        /* When less than 10 seconds show timer with extra zero*/
        if (miliseconds < 10000) {
            document.getElementById("timer").innerHTML = '0:0' + miliseconds/1000;
        }

        /* When less than 1 minute show timer with no decimal zero*/
        else {
            document.getElementById("timer").innerHTML = '0:' + miliseconds/1000;
        }

        /* When time ends up */
        if (miliseconds <= 0) {
            clearInterval(timer);
            document.getElementById("timer").innerHTML = '0:0' + miliseconds/1000;
        }

        /* When user finds all 15 pairs before timer ends */
        if (miliseconds > 0 && pairCount === 15) {
            clearInterval(timer);

            /* Add 15 points */
            user_points += 15;
            setTimeout(function() { $("#points").text(user_points); }, 300);

            /* Update hidden input form in modal with users points */
            $(".points_input").val(user_points);

            /* Show modal */
            $("#modalTitle").text("Congratulations!!")
            $("#modalBody").text("Looks like you're a master at this game!")
            setTimeout(function() { $("#staticBackdrop").modal(); }, 1000);
        }

        /* When user does not find all 15 pairs before timer ends */
        else if (miliseconds <= 0 && pairCount <= 15) {
            clearInterval(timer);

            /* When user has 10 points or more, subtract 10 points  */
            if (user_points >= 10) {
                user_points -= 10;
            }

            /* When user has less than 10 points, reset points to 0 */
            else {
                user_points = 0;
            }

            setTimeout(function() { $("#points").text(user_points); }, 300);

            /* Update hidden input form in modal with users points */
            $(".points_input").val(user_points);

            /* Show modal */
            $("#modalTitle").text("Ups!!")
            $("#modalBody").text("Looks like you couldn't find all the pairs. Better luck next time!")
            setTimeout(function() { $("#staticBackdrop").modal(); }, 1000);
        }
    }


    /* Card Flipper Function */
    $(".flip-card").click(function() {

        /* Start countdown when the first card is flipped */
        if (countDownStarted === false) {
            countDownStarted = true;
            timer = setInterval(countDown, 1000);
        }

        /* If a card is clicked, and it wasn't already flipped */
        if ($(this).attr("id") !== 'flipped1' && $(this).attr("id") !== 'found' && clickEnabled) {

            /* Start click count */
            clickCount += 1;

            /* Register which card was flipped */
            if (clickCount === 1) {

                /* Flip card to show hidden side */
                $(this).toggleClass('flip-rotate');

                /* Temporarily change first card id to flipped */
                card1originalID = $(this).attr("id");
                $(this).attr("id", 'flipped1');
            }

            /* When second card is flipped and it doesn't match the first */
        	else if (clickCount === 2 && $(this).attr("id") !== card1originalID) {

                /* Flip card to show hidden side */
        	    $(this).toggleClass('flip-rotate');

                /* Temporarily change second card id to flipped */
                var card2originalID = $(this).attr("id");
                $(this).attr("id", 'flipped2');

                /* Animate both cards to reverse to unmarked side */
                setTimeout(function(){ $("#flipped1").toggleClass('flip-rotate'); }, 600);
                setTimeout(function(){ $("#flipped1").attr("id", card1originalID); }, 600);
                setTimeout(function(){ $("#flipped2").toggleClass('flip-rotate'); }, 600);
                setTimeout(function(){ $("#flipped2").attr("id", card2originalID); }, 600);

                /* Do not let user click until cards are reversed unmarked side */
                clickEnabled = false;
                setTimeout(function(){ clickEnabled = true }, 600);

                /* Set pair count to zero */
                clickCount = 0;
        	}

            /* When second card is flipped and it does match the first */
            else if (clickCount === 2 && $(this).attr("id") === card1originalID) {

                /* Flip card to show hidden side */
                $(this).toggleClass('flip-rotate');

                /* Change id of both cards to found */
                $("#flipped1").attr("id", 'found');
                $(this).attr("id", 'found');

                /* Set pair count to zero */
                clickCount = 0;

                /* Count pairs */
                setTimeout(function() { pairCount += 1; }, 300);

                /* Add points */
                setTimeout(function() { user_points += 2; }, 300);
                setTimeout(function() { $("#points").text(user_points); }, 300);
            }
        }
    });
});


/* When screen is smaller than 480px insert line break in footer */
setInterval(function () {
    if ($(window).width() <= 480) {
        document.getElementById('linebreak').innerHTML = '<br>';
    }
}, 1000);