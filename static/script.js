// Exemple : Gestion des uploads avec feedback visuel
document.querySelector('form').addEventListener('submit', function(e) {
    e.preventDefault();
    const fileInput = document.querySelector('input[type="file"]');
    const file = fileInput.files[0];

    if (!file) {
        alert("Veuillez sélectionner un fichier.");
        return;
    }

    // Afficher un spinner
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    this.appendChild(spinner);

    // Soumettre le formulaire
    this.submit();
});
