function funk(id) {
    let divName = id + '-display';
    let elem = document.getElementById(divName);
    if ( id == 'other') {
        let contractSwitch = document.getElementById('contract-switch');
        if (contractSwitch.classList.contains('display-none')) {
            contractSwitch.classList.remove('display-none');
            elem.style.display = 'none';
            return;
        }
        else {
            contractSwitch.classList.add('display-none');
            if (elem != null) {
                if (elem.style.display == 'block') {
                    elem.style.display ='none';
                    return;
                }
                elem.style.display = 'block';                
            }
        }
        }

    if (id == 'contract') {
        let otherSwitch = document.getElementById('other-switch');
        if (otherSwitch.classList.contains('display-none')) {
            otherSwitch.classList.remove('display-none');
            elem.style.display = 'none';
            return;
        }
        else {
            otherSwitch.classList.add('display-none');
            if (elem != null) {
                if (elem.style.display == 'block') {
                    elem.style.display ='none';
                    return;
                }
                elem.style.display = 'block';                
            }
        }
    }
}


const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))
const popover = new bootstrap.Popover('.popover-dismiss', {
    trigger: 'focus'
  })
