$(document).ready(function() {
    var session_id = Math.random().toString(36).substring(2, 15); // Gerar ID de sessão aleatório

    $("#send_button").click(function() {
        var user_input = $("#user_input").val();

        // Exibir a mensagem do usuário
        $("#chatbox").append("<p><b>Usuário:</b> " + user_input + "</p>");

        // Limpar o campo de entrada
        $("#user_input").val("");

        // Enviar a mensagem para o Flask
        $.ajax({
            url: "/get_answer",
            method: "POST",
            data: {msg: user_input, session_id: session_id},
            success: function(response) {
                // Exibir a resposta do bot
                $("#chatbox").append("<p><b>Assistente:</b> " + response.answer + "</p>");

                // Rolar para o final da caixa de chat
                $("#chatbox").scrollTop($("#chatbox")[0].scrollHeight);
            },
            error: function(error) {
                console.error("Erro ao obter resposta:", error);
            }
        });
    });

    // Adicionar um listener para a tecla Enter
    $("#user_input").keypress(function(event) {
        if (event.which === 13) { // Tecla Enter
            $("#send_button").click();
        }
    });
});