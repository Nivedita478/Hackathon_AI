function getData() {

    return {

        soil_ph:
            Number(document.getElementById("soil_ph").value),

        carbon:
            Number(document.getElementById("carbon").value),

        moisture:
            Number(document.getElementById("moisture").value),

        rainfall:
            Number(document.getElementById("rainfall").value),

        temperature:
            Number(document.getElementById("temperature").value),

        species:
            Number(document.getElementById("species").value),

        habitat:
            Number(document.getElementById("habitat").value),

        pollution:
            Number(document.getElementById("pollution").value),

        deforestation:
            Number(document.getElementById("deforestation").value)

    };
}


async function analyze() {

    const response = await fetch(
        "/analyze",
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(getData())

        }
    );

    const result =
        await response.json();


    document.getElementById("score")
        .innerText =
        result.score;


    document.getElementById("status")
        .innerText =
        result.status;


    let riskHTML = "";


    if (result.risks.length === 0) {

        riskHTML =
            "<p>No major combined risk detected.</p>";

    } else {

        result.risks.forEach(
            risk => {

                riskHTML += `

                <div class="risk">

                    <strong>
                        ${risk.title}
                    </strong>

                    <br>

                    Severity:
                    ${risk.severity}

                    <br>

                    Metrics:
                    ${risk.metrics}

                </div>

                `;

            }
        );

    }


    document.getElementById("risks")
        .innerHTML =
        riskHTML;


    let recommendationHTML = "";


    result.recommendations.forEach(
        item => {

            recommendationHTML += `

            <div class="recommendation">

                <h3>
                    🌱 ${item.action}
                </h3>

                <p>
                    <strong>
                        Why:
                    </strong>
                    ${item.reason}
                </p>

                <p>
                    <strong>
                        Impacted metrics:
                    </strong>
                    ${item.metrics.join(", ")}
                </p>

                <p>
                    <strong>
                        Time horizon:
                    </strong>
                    ${item.time}
                </p>

                <p class="source">

                    📚 Evidence:
                    ${item.source}

                </p>

            </div>

            `;

        }
    );


    document.getElementById(
        "recommendations"
    ).innerHTML =
        recommendationHTML;

}


async function simulate() {

    const data = getData();

    data.intervention =
        document.getElementById(
            "intervention"
        ).value;


    const response = await fetch(
        "/simulate",
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(data)

        }
    );


    const result =
        await response.json();


    const change =
        result.change;


    let message = "";

    if (change > 0) {

        message =
            `📈 Ecological score could increase by ${change} points.`;

    } else if (change < 0) {

        message =
            `📉 Ecological score could decrease by ${Math.abs(change)} points.`;

    } else {

        message =
            "The simulated intervention produces little score change.";

    }


    document.getElementById(
        "simulation"
    ).innerHTML = `

        <strong>
            Before:
        </strong>

        ${result.before}/100

        <br><br>

        <strong>
            After:
        </strong>

        ${result.after}/100

        <br><br>

        ${message}

    `;

}


async function askAI() {

    const message =
        document.getElementById(
            "question"
        ).value;


    if (!message.trim()) {

        return;

    }


    document.getElementById(
        "answer"
    ).innerText =
        "🔎 Searching scientific knowledge...";


    const response = await fetch(
        "/chat",
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify({
                    message: message
                })

        }
    );


    const result =
        await response.json();


    document.getElementById(
        "answer"
    ).innerText =
        result.answer;

}