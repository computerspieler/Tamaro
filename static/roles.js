function click_handler(elt) {
    const role = elt.value;
    
    fetch("/get-id?role=" + role, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        }
    })
        .then((res) => {
            res.json().then((res) => {
                window.location.replace("/question?role=" + role + "&id=" + res["id"]);
            });
        })
        .catch(() => {
            console.error("Unable to fetch and ID");
        });
}
