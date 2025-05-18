const urlParams = new URLSearchParams(window.location.search);
const role = urlParams.get('role');
const id = urlParams.get('id');
let values = [];

async function getQuestionsRate() {
    let container = document.getElementById("questions");
    
    let res = await (await fetch("/get-questions?role="+role)).json();

    let slides = [];
    for(let q of res) {
        let question_container = document.createElement("div");
        {
            let question_lbl = document.createElement("h4");
            question_lbl.textContent = q;
            question_container.appendChild(question_lbl);
        }
        let slider_container = document.createElement("div");
        slider_container.className = "sliderContainer";
        {
            let lbl_left = document.createElement("div");
            lbl_left.textContent = "Pas d'accord";
            slider_container.appendChild(lbl_left);

            let resp_slider = document.createElement("input");
            resp_slider.type="range";
            resp_slider.min="1";
            resp_slider.max="5";
            resp_slider.value="3";
            
            slides.push(resp_slider);
            slider_container.appendChild(resp_slider);

            let lbl_right = document.createElement("div");
            lbl_right.textContent = "Absolument d'accord";
            slider_container.appendChild(lbl_right);
        }
        question_container.appendChild(slider_container);

        container.appendChild(question_container);
    }

    return slides;
}

async function associateWithUser(user) {
    let res = await fetch("/associate", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            me: id,
            them: user
        })
    });

    return [(res.status == 200), (res.status == 404)];
}

async function moveOn(them) {
    if(values.length == 0) {
        console.log("No values, but want to move on");
        return;
    }

    let res = await fetch("/answers", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: id,
            answers: values
        })
    });

    if(res.status != 200) {
        console.error("Error: ");
        console.error(e);
        return;
    }

    window.location.replace("/response?id=" + id + "&role=" + role);
}

function userNotFound(user) {
    let user_not_found = document.getElementById("user_not_found");
    user_not_found.hidden = false;
    user_not_found.textContent = "L'utilisateur '" + user + "' n'a pas été trouvé";
}

function waitForOtherUser() {
    fetch("/has-associated", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id: id
        })
    }).then(async (res_raw) => {
        let res = await res_raw.json();
        if(!res) return;
        moveOn(res);
    })
}


getQuestionsRate().then((slides) => {
    let end_button = document.getElementById("fini");
    end_button.addEventListener("click", () => {
        values = slides.map((x) => x.value);
        
        document.getElementById("questions").hidden = true;
        end_button.hidden = true;
        {
            let your_textbox = document.createElement("div");
            your_textbox.textContent = "Entrez l'ID de votre partenaire (ou attendez que votre partenaire le fasse).";
            document.body.appendChild(your_textbox);

            let your_textbox2 = document.createElement("h3");
            your_textbox2.textContent = "Votre ID est : " + id;
            document.body.appendChild(your_textbox2);
            
            let partner_code = document.createElement("textarea");
            document.body.appendChild(partner_code);
            document.body.appendChild(document.createElement("br"));

            let done_button = document.createElement("button");
            done_button.textContent = "J'ai fini !";
            done_button.addEventListener("click", () => {
                console.log(partner_code.value);
                associateWithUser(partner_code.value)
                    .then((res) => {
                        if(res[0]) moveOn(partner_code.value);
                        if(res[1]) userNotFound(partner_code.value);
                    })
                    .catch(() => {});
            });
            document.body.appendChild(done_button);

            setInterval(waitForOtherUser, 500);

            let user_not_found = document.createElement("div");
            user_not_found.id = "user_not_found";
            user_not_found.hidden = true;
            document.body.appendChild(user_not_found);
        }
    })
});
