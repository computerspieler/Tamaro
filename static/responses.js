const urlParams = new URLSearchParams(window.location.search);
const role = urlParams.get('role');
const id = urlParams.get('id');

async function getAnswers() {
    let resq = await (await fetch("/get-questions?role="+role)).json();
    let resa = await (await fetch("/answers?id="+id)).json();

    for(let i = 0; i < resq.length; i ++) {
        let question = document.createElement("h3");
        question.textContent = resq[i];
        document.body.appendChild(question);

        let answer = document.createElement("div");
        answer.textContent = resa[0][i];
        document.body.appendChild(answer);

        document.body.appendChild(document.createElement("br"));
    }


    let answer = document.createElement("h1");
    answer.textContent = "Votre écart moyen est de: " + resa[1];
    document.body.appendChild(answer);
}

getAnswers();