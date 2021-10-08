// Control functions for the basic stepper motor controller screen.

async function postData(url = '', data = {}) {
    // Default options are marked with *
    const response = await fetch(url, {
        method: 'POST', // *GET, POST, PUT, DELETE, etc.
        mode: 'cors', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            // 'Content-Type': 'application/x-www-form-urlencoded',
        },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: JSON.stringify(data) // body data type must match "Content-Type" header
    });
    return response.json(); // parses JSON response into native JavaScript objects
}

function fix_move_increments() {
    // Limit the movement increments based on the selected movement type
    const moveType = document.querySelector("#movement-type-select")
    const moveTypeSelected = moveType.options[moveType.selectedIndex].value;
    const moveIncerement = document.querySelector("#movement-amount-select")
    const moveAmount = document.querySelector("#movement-amount-select")

    if (moveType.selectedIndex === 0) {
        // TODO - Some sort of feedback here.
        return
    }

    const incrementTypes = {
        "move_mm": 0.001,
        "move_steps": 1,
        "move_rotations": 0.001
    }
    moveAmount.setAttribute("step", incrementTypes[moveTypeSelected])
    moveAmount.setAttribute("value", 0)

}

async function change_direction(direction) {
    // Send a post request to change the direction of the current motor.
    const motorSelect = document.querySelector("#stepper-select")
    const motorSelectValue = motorSelect.options[motorSelect.selectedIndex].value;
    const logCard = document.querySelector("#log-card")
    let url = document.body.changeDirectionUrl
    url = url.substring(0, url.lastIndexOf("/") + 1) + motorSelectValue

    if (motorSelectValue === "Select a stepper motor") {
        const newLog = "<p style='color: red'>Select a stepper motor!</p>"
        logCard.innerHTML = newLog + logCard.innerHTML
    }

    const data = {
        "motor_id": motorSelectValue,
        "property": "direction_of_rotation",
        "value": direction,
        "csrfmiddlewaretoken": document.querySelector('[name=csrfmiddlewaretoken]').value
    }
    const response = await postData(url, data)

    // Log the output to the log card.
    if ("error" in response) {
        const newLog = "<p style='color: red'>" + response["error"] + "</p>"
        logCard.innerHTML = newLog + logCard.innerHTML
    } else {
        const newLog = "<p style='color: green'>" + response["log"] + "</p>"
        logCard.innerHTML = newLog + logCard.innerHTML
    }
}

async function send_move() {
    // Send a post request to send a move command to the motor.
    const motorSelect = document.querySelector("#stepper-select")
    const motorSelectValue = motorSelect.options[motorSelect.selectedIndex].value;
    let url = document.body.stepperMotorMoveURL
    url = url.substring(0, url.lastIndexOf("/") + 1) + motorSelectValue
    const logCard = document.querySelector("#log-card")
    const movementTypeSelect = document.querySelector("#movement-type-select")
    const movementAmountSelect = document.querySelector("#movement-amount-select")

    let moveAmount = movementAmountSelect.value
    if (moveAmount.search(".")) {
        moveAmount = parseFloat(moveAmount)
    } else {
        moveAmount = parseInt(moveAmount)
    }

    const data = {
        "motor_id": motorSelectValue,
        "movement_type": movementTypeSelect.value,
        "movement_amount": moveAmount,
        "csrfmiddlewaretoken": document.querySelector('[name=csrfmiddlewaretoken]').value
    }
    const response = await postData(url, data)

    // Log the output to the log card.
    if ("error" in response) {
        const newLog = "<p style='color: red'>" + response["error"] + "</p>"
        logCard.innerHTML = newLog + logCard.innerHTML
    } else {
        const newLog = "<p style='color: green'>" + response["log"] + "</p>"
        logCard.innerHTML = newLog + logCard.innerHTML
    }
}