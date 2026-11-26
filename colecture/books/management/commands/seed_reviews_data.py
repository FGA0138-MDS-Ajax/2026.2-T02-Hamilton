"""Dados e lógica de seed de avaliações (BookReview) para o catálogo de livros.

Utilizado por `seed_books` e `seed_demo` para garantir que todos os livros
tenham resenhas e notas realistas de leitores da plataforma.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Profile
from accounts.services import AccountService
from books.models import Book, BookReview

# Lista padronizada dos 10 usuários de demonstração e autores das resenhas
SEED_USERS = [
    "ana",
    "bruno",
    "carla",
    "diego",
    "elisa",
    "felipe",
    "gabriela",
    "heitor",
    "isabela",
    "joao",
]

DEFAULT_PASSWORD = "Senha#123"

# Resenhas para todos os 82 livros do catálogo
# Formato: {isbn: [(username, rating, review_text), ...]}
# Cada resenha respeita o limite de 300 caracteres do model BookReview
# e utiliza notas válidas com intervalo de 1.
BOOK_REVIEWS = {
    # --- Ficção científica ---
    "9780451524935": [  # 1984
        ("ana", Decimal("5.0"), "Uma distopia assustadoramente atual. O controle da verdade e da linguagem pelo Grande Irmão causa calafrios do início ao fim."),
        ("felipe", Decimal("4.0"), "Obra-prima incontornável da ficção especulativa. A atmosfera opressiva de Londres sob o Socing é magistralmente construída."),
    ],
    "9780060850524": [  # Admirável Mundo Novo
        ("bruno", Decimal("5.0"), "Contraste fascinante com 1984: aqui a dominação não vem pela dor, mas pelo prazer fabricado e condicionamento. Leitura indispensável."),
        ("gabriela", Decimal("4.0"), "Provocativo e atemporal. A crítica à busca desenfreada pela felicidade artificial ressoa muito hoje."),
    ],
    "9781451673319": [  # Fahrenheit 451
        ("carla", Decimal("5.0"), "Uma ode comovente ao valor dos livros e da memória humana. A transformação de Guy Montag é inspiradora."),
        ("isabela", Decimal("4.0"), "Poético e urgente. Bradbury nos lembra da importância do pensamento crítico e da literatura."),
    ],
    "9780441172719": [  # Duna
        ("felipe", Decimal("5.0"), "O ápice do worldbuilding na ficção científica. Política, religião, ecologia e intrigas galácticas em Arrakis."),
        ("ana", Decimal("5.0"), "Simplesmente épico. Paul Atreides e os mistérios dos Fremen e dos vermes da areia prendem a atenção o tempo todo."),
    ],
    "9780441569595": [  # Neuromancer
        ("joao", Decimal("5.0"), "O marco do cyberpunk! Prosa densa, estética neon e visão profética da internet e inteligência artificial."),
        ("diego", Decimal("4.0"), "Clássico revolucionário. Case e Molly formam uma dupla inesquecível na trama cheia de ação no ciberespaço."),
    ],
    "9780812550702": [  # O Jogo do Exterminador
        ("diego", Decimal("5.0"), "Ritmo frenético e um final surpreendente. As estratégias de batalha e a psicologia de Ender são brilhantes."),
        ("bruno", Decimal("4.0"), "Muito mais profundo do que aparenta. Questiona as consequências éticas da liderança sob pressão extrema."),
    ],
    "9780553293357": [  # Fundação
        ("felipe", Decimal("5.0"), "A psico-história de Hari Seldon é uma das ideias mais geniais da literatura. Asimov em sua melhor forma."),
        ("joao", Decimal("4.0"), "Uma grandiosa ópera espacial focada na sociologia e na evolução das civilizações ao longo dos séculos."),
    ],
    "9780345391803": [  # O Guia do Mochileiro das Galáxias
        ("elisa", Decimal("5.0"), "Hilário, inteligente e absurdamente criativo. Não entre em pânico e nunca esqueça sua toalha!"),
        ("heitor", Decimal("4.0"), "Humor britânico afiado aplicado à ficção científica. Impossível ler sem dar boas gargalhadas."),
    ],
    "9780385333849": [  # Matadouro 5
        ("heitor", Decimal("4.0"), "Sátira antibélica comovente e surreal. A estrutura não linear de Billy Pilgrim reflete o trauma da guerra com perfeição."),
        ("carla", Decimal("5.0"), "Assim caminha a humanidade. Vonnegut mescla dor e ironia de um jeito único e inesquecível."),
    ],
    "9780385490818": [  # O Conto da Aia
        ("carla", Decimal("5.0"), "Narrativa visceral e perturbadora sobre autoritarismo e controle sobre os corpos. Atwood escreve com maestria."),
        ("ana", Decimal("4.0"), "Leitura tensa e necessária. O diário de Offred em Gilead emociona e desperta reflexões profundas."),
    ],
    "9780486282114": [  # Frankenstein
        ("isabela", Decimal("5.0"), "Mary Shelley criou uma obra profundamente humana sobre solidão, rejeição e a responsabilidade da ciência."),
        ("bruno", Decimal("4.0"), "Muito superior aos mitos do cinema. A criatura de Victor Frankenstein é articulada, trágica e complexa."),
    ],
    "9780345539434": [  # Cosmos
        ("joao", Decimal("5.0"), "Carl Sagan transmite paixão pela ciência em cada parágrafo. Inspirador, poético e esclarecedor."),
        ("gabriela", Decimal("5.0"), "Um livro que expande os horizontes da mente. Somos poeira de estrelas contemplando o próprio cosmos."),
    ],

    # --- Fantasia ---
    "9780547928227": [  # O Hobbit
        ("bruno", Decimal("5.0"), "Uma introdução perfeita à Terra-média. A jornada inesperada de Bilbo Bolseiro aquece o coração."),
        ("elisa", Decimal("4.0"), "Leve, divertido e cativante. Os enigmas no escuro com o Gollum são o ponto alto da aventura!"),
    ],
    "9780618346257": [  # A Sociedade do Anel
        ("bruno", Decimal("5.0"), "O padrão ouro da fantasia épica. A descrição das paisagens, o peso do Anel e a irmandade são magistrais."),
        ("heitor", Decimal("4.0"), "Riqueza mitológica sem igual. Cada detalhe construído por Tolkien faz a Terra-média parecer real."),
    ],
    "9780590353427": [  # Harry Potter e a Pedra Filosofal
        ("elisa", Decimal("5.0"), "A magia de descobrir Hogwarts nunca envelhece. Um início encantador para uma saga inesquecível."),
        ("isabela", Decimal("4.0"), "História aconchegante sobre amizade, coragem e pertencimento. Excelente para todas as idades."),
    ],
    "9780553593716": [  # A Guerra dos Tronos
        ("diego", Decimal("5.0"), "Trama política intrincada, reviravoltas chocantes e personagens moralmente cinzentos. Viciante!"),
        ("felipe", Decimal("4.0"), "George R. R. Martin reinventou a fantasia sombria com diálogos afiados e imprevisibilidade constante."),
    ],
    "9780756404741": [  # O Nome do Vento
        ("bruno", Decimal("5.0"), "A prosa lírica de Patrick Rothfuss é deslumbrante. Acompanhar a juventude de Kvothe é pura magia."),
        ("elisa", Decimal("4.0"), "Sistema de magia fascinante e um protagonista lendário contando sua própria história sem rodeios."),
    ],
    "9780439023528": [  # Jogos Vorazes
        ("carla", Decimal("5.0"), "Ritmo implacável e forte crítica social. Katniss Everdeen é uma protagonista admirável e destemida."),
        ("diego", Decimal("4.0"), "Distopia eletrizante que prende a atenção do primeiro ao último capítulo. Impossível parar de ler."),
    ],
    "9780060934347": [  # Dom Quixote
        ("heitor", Decimal("5.0"), "Um dos maiores romances da humanidade. O contraste entre o idealismo de Quixote e a sanidade de Sancho é eterno."),
        ("ana", Decimal("4.0"), "Divertido e melancólico ao mesmo tempo. Uma reflexão imortal sobre loucura, imaginação e nobreza de espírito."),
    ],
    "9780156012195": [  # O Pequeno Príncipe
        ("isabela", Decimal("5.0"), "O essencial é invisível aos olhos. Uma fábula poética e comovente que ensina sobre amor e afeto."),
        ("gabriela", Decimal("4.0"), "Pequeno no tamanho, monumental na sensibilidade. Um lembrete tocante de não esquecermos nossa criança interior."),
    ],

    # --- Romance / Literatura clássica ---
    "9780743273565": [  # O Grande Gatsby
        ("ana", Decimal("5.0"), "Retrato brilhante da ilusão do sonho americano nos anos 20. A escrita lírica de Fitzgerald é deslumbrante."),
        ("isabela", Decimal("4.0"), "A obsessão de Jay Gatsby e a frivolidade da alta sociedade são retratadas com elegância e melancolia."),
    ],
    "9780141439518": [  # Orgulho e Preconceito
        ("carla", Decimal("5.0"), "Jane Austen em seu auge. Os diálogos inteligentes entre Elizabeth Bennet e o Sr. Darcy são insuperáveis."),
        ("elisa", Decimal("4.0"), "Romance atemporal e ironia fina sobre as convenções sociais da Inglaterra do século XIX. Apaixonante."),
    ],
    "9780141441146": [  # Jane Eyre
        ("isabela", Decimal("4.0"), "A força interior e a integridade moral de Jane Eyre tornam esta obra uma das mais marcantes da era vitoriana."),
        ("carla", Decimal("5.0"), "Gótico, misterioso e apaixonado. O segredo de Thornfield Hall mantém o suspense até o desfecho."),
    ],
    "9780141439556": [  # O Morro dos Ventos Uivantes
        ("carla", Decimal("4.0"), "A paixão destrutiva entre Heathcliff e Catherine é crua e tempestuosa como os ermos de Yorkshire."),
        ("ana", Decimal("5.0"), "Personagens imperfeitos e intensos. Emily Brontë criou um romance gótico sem concessões ao leitor."),
    ],
    "9780142437247": [  # Moby Dick
        ("heitor", Decimal("4.0"), "A obsessão do Capitão Ahab pela baleia branca é uma grandiosa alegoria sobre os limites humanos e o destino."),
        ("felipe", Decimal("4.0"), "Denso e detalhado, mas os momentos épicos de confronto em alto mar recompensam cada página."),
    ],
    "9780143107637": [  # Crime e Castigo
        ("diego", Decimal("5.0"), "Mergulho profundo e perturbador na psique de Raskólnikov. Dostoiévski disseca a culpa como ninguém."),
        ("heitor", Decimal("5.0"), "Obra monumental. O suspense psicológico e a busca por redenção em São Petersburgo marcam para sempre."),
    ],
    "9780374528379": [  # Os Irmãos Karamázov
        ("heitor", Decimal("5.0"), "O ápice do romance filosófico. As conversas de Ivan e Aliócha e o Grande Inquisidor são momentos sublimes."),
        ("bruno", Decimal("5.0"), "Fé, razão, moralidade e família. Uma leitura densa e transformadora que exige entrega total."),
    ],
    "9780143035008": [  # Anna Karenina
        ("carla", Decimal("5.0"), "Tolstói cria personagens com riqueza emocional incomparável. O contraste entre Anna e Levin enriquece a trama."),
        ("isabela", Decimal("5.0"), "Todas as famílias felizes se parecem. Um retrato deslumbrante e trágico da alta sociedade russa."),
    ],
    "9781400079988": [  # Guerra e Paz
        ("heitor", Decimal("3.0"), "Um panorama épico das guerras napoleônicas e das paixões humanas. Leitura desafiadora e recompensadora."),
        ("felipe", Decimal("4.0"), "A escala grandiosa da obra impressiona. Pierre Bezukhov é um dos melhores personagens da história literária."),
    ],
    "9780451419439": [  # Os Miseráveis
        ("bruno", Decimal("5.0"), "A jornada de redenção de Jean Valjean e a perseguição de Javert comovem e inspiram do começo ao fim."),
        ("carla", Decimal("5.0"), "Um manifesto monumental sobre justiça social, compaixão e amor ao próximo. Indispensável."),
    ],
    "9780060883287": [  # Cem Anos de Solidão
        ("ana", Decimal("5.0"), "O realismo mágico em sua plenitude. A saga dos Buendía em Macondo é hipnótica, poética e inesquecível."),
        ("gabriela", Decimal("4.0"), "García Márquez constrói um universo único onde o fantástico se integra com naturalidade à vida cotidiana."),
    ],
    "9780316769488": [  # O Apanhador no Campo de Centeio
        ("diego", Decimal("4.0"), "A voz autêntica e rebelde de Holden Caulfield traduz com maestria as angústias da adolescência."),
        ("elisa", Decimal("4.0"), "Retrato sincero da solidão e do estranhamento diante da falsidade do mundo adulto."),
    ],
    "9780061120084": [  # O Sol é Para Todos
        ("ana", Decimal("5.0"), "Atticus Finch ensina lições atemporais de coragem, integridade e empatia através do olhar puro de Scout."),
        ("gabriela", Decimal("5.0"), "Emocionante e essencial. Trata de preconceito e justiça com delicadeza e força moral impactantes."),
    ],
    "9780399501487": [  # O Senhor das Moscas
        ("diego", Decimal("3.0"), "Visão sombria e realista da natureza humana quando despida das regras e convenções da civilização."),
        ("heitor", Decimal("4.0"), "A descida dos garotos à barbárie na ilha deserta é angustiante e provocativa."),
    ],
    "9780451526342": [  # A Revolução dos Bichos
        ("ana", Decimal("5.0"), "Fábula alegórica brilhante sobre como ideais nobres podem ser corrompidos pelo poder e pelo autoritarismo."),
        ("joao", Decimal("4.0"), "Todos os animais são iguais, mas alguns são mais iguais. Uma lição histórica que permanece atual."),
    ],
    "9781451626650": [  # Ardil-22
        ("joao", Decimal("5.0"), "A lógica absurda da burocracia militar é satirizada com inteligência brilhante por Heller."),
        ("diego", Decimal("4.0"), "Divertido e desconcertante. O capitão Yossarian sintetiza o desespero do indivíduo perante o sistema."),
    ],
    "9781400033416": [  # Amada
        ("isabela", Decimal("5.0"), "Toni Morrison escreve uma obra devastadora sobre a herança traumática da escravidão e o amor materno."),
        ("carla", Decimal("4.0"), "Prosa poética poderosa e personagens profundos. Uma das leituras mais marcantes do século XX."),
    ],
    "9780062315007": [  # O Alquimista
        ("gabriela", Decimal("4.0"), "Uma história simples e inspiradora sobre seguir nossos sonhos e prestar atenção aos sinais da vida."),
        ("elisa", Decimal("4.0"), "Narrativa fluida com mensagens motivadoras sobre persistência e autodescoberta."),
    ],
    "9780486411095": [  # Drácula
        ("diego", Decimal("4.0"), "O formato epistolar cria uma atmosfera gótica tensa e misteriosa. O Conde Drácula é aterrorizante."),
        ("bruno", Decimal("4.0"), "O nascimento do horror vampírico moderno. A viagem à Transilvânia e a caçada em Londres são impecáveis."),
    ],

    # --- Mistério / Suspense ---
    "9780062073488": [  # E Não Sobrou Nenhum
        ("diego", Decimal("5.0"), "A engrenagem do suspense de Agatha Christie é perfeita. Dez suspeitos em uma ilha isolada e final surpreendente!"),
        ("carla", Decimal("4.0"), "Ritmo tenso e desfecho genial. Definitivamente um dos maiores clássicos do mistério policial."),
    ],
    "9780062693662": [  # Assassinato no Expresso do Oriente
        ("diego", Decimal("5.0"), "Hercule Poirot demonstrando todo o poder das suas células cinzentas em um mistério elegante no trem de luxo."),
        ("isabela", Decimal("4.0"), "A solução engenhosa e o dilema moral apresentado tornam este livro um marco da literatura policial."),
    ],
    "9780307474278": [  # O Código Da Vinci
        ("felipe", Decimal("4.0"), "Capítulos curtos, ganchos viciantes e ritmo de cinema. Robert Langdon mantém a adrenalina em alta."),
        ("diego", Decimal("3.0"), "Leitura ágil e divertida, cheia de enigmas em museus e igrejas históricas europeias."),
    ],
    "9780307588371": [  # Garota Exemplar
        ("carla", Decimal("5.0"), "Thriller psicológico perturbador e brilhante sobre aparências, mentiras e a toxicidade conjugal."),
        ("diego", Decimal("4.0"), "Reviravolta sensacional no meio do livro. Personagens fascinantes e uma narrativa muito afiada."),
    ],
    "9780307454546": [  # Os Homens que Não Amavam as Mulheres
        ("diego", Decimal("5.0"), "Lisbeth Salander é uma personagem icônica da literatura moderna. Trama investigativa densa e eletrizante."),
        ("felipe", Decimal("4.0"), "Mikael Blomkvist e Salander formam uma parceria dinâmica inesquecível no suspense nórdico."),
    ],

    # --- Biografia / Memórias ---
    "9780553296983": [  # O Diário de Anne Frank
        ("ana", Decimal("5.0"), "O testemunho inocente e sensível de uma jovem garota em meio ao horror da guerra. Comovente e eterno."),
        ("isabela", Decimal("5.0"), "Leitura indispensável para a humanidade. A esperança de Anne Frank resiste mesmo diante da barbárie."),
    ],
    "9780316548182": [  # Long Walk to Freedom
        ("heitor", Decimal("5.0"), "A inspiradora trajetória de Nelson Mandela contra o apartheid. Uma lição sublime de perdão e estadismo."),
        ("gabriela", Decimal("4.0"), "A resiliência de Mandela ao longo de décadas na prisão emociona e demonstra a força da convicção moral."),
    ],
    "9781451648539": [  # Steve Jobs
        ("joao", Decimal("5.0"), "Walter Isaacson equilibra genialidade e temperamento difícil em uma biografia honesta e detalhada."),
        ("gabriela", Decimal("4.0"), "Visão instigante sobre inovação, interseção entre arte e tecnologia, e a busca incansável por excelência."),
    ],
    "9780399590504": [  # Educated
        ("gabriela", Decimal("5.0"), "O relato corajoso de Tara Westover sobre como a educação transformou sua vida e libertou seu pensamento."),
        ("isabela", Decimal("4.0"), "Memórias intensas e inspiradoras sobre superação familiar e a busca pela própria identidade."),
    ],
    "9781524763138": [  # Minha História
        ("carla", Decimal("5.0"), "Michelle Obama compartilha com sinceridade sua infância humilde, carreira e os bastidores da Casa Branca."),
        ("ana", Decimal("4.0"), "Escrita calorosa e inspiradora sobre determinação, autenticidade e serviço público."),
    ],
    "9780807014295": [  # Em Busca de Sentido
        ("heitor", Decimal("5.0"), "Viktor Frankl mostra que, mesmo nas piores circunstâncias, o ser humano pode encontrar propósito para viver."),
        ("gabriela", Decimal("5.0"), "Livro transformador. A logoterapia e o relato dos campos de concentração tocam o âmago da alma humana."),
    ],

    # --- História / Ciências Humanas ---
    "9780062316097": [  # Sapiens
        ("heitor", Decimal("5.0"), "Síntese brilhante da trajetória humana desde as savanas até a inteligência artificial. Muito provocador."),
        ("felipe", Decimal("4.0"), "Harari desafia premissas estabelecidas com elegância e clareza. Leitura fundamental para entender nossa espécie."),
    ],
    "9780062464316": [  # Homo Deus
        ("felipe", Decimal("5.0"), "Reflexão instigante sobre o futuro da biotecnologia, algoritmos e a evolução da humanidade."),
        ("joao", Decimal("4.0"), "Visão visionária sobre dados e tecnologia transformando o significado de ser humano no século XXI."),
    ],
    "9780525512172": [  # 21 Lições para o Século 21
        ("heitor", Decimal("4.0"), "Ensaios objetivos e perspicazes sobre inteligência artificial, notícias falsas e nacionalismo hoje."),
        ("ana", Decimal("4.0"), "Provoca reflexões necessárias sobre os desafios mais urgentes do nosso presente conturbado."),
    ],
    "9780393354324": [  # Armas, Germes e Aço
        ("heitor", Decimal("5.0"), "Jared Diamond desconstrói preconceitos ao explicar o destino das civilizações pela geografia e biologia."),
        ("felipe", Decimal("4.0"), "Abordagem interdisciplinar fascinante conectando história, agricultura e biogeografia."),
    ],
    "9780553380163": [  # Uma Breve História do Tempo
        ("joao", Decimal("4.0"), "Stephen Hawking torna a física teórica e a cosmologia acessíveis ao público leigo com metáforas brilhantes."),
        ("gabriela", Decimal("5.0"), "Uma fascinante jornada sobre a origem do tempo, buracos negros e o destino do universo."),
    ],
    "9780374533557": [  # Rápido e Devagar
        ("gabriela", Decimal("4.0"), "Kahneman desvenda os vieses cognitivos e os dois sistemas de pensamento de forma brilhante."),
        ("heitor", Decimal("5.0"), "Essencial para quem deseja compreender como a mente toma decisões e evita armadilhas do raciocínio."),
    ],

    # --- Desenvolvimento Pessoal / Negócios ---
    "9780735211292": [  # Hábitos Atômicos
        ("gabriela", Decimal("5.0"), "Mudanças de 1% geram resultados extraordinários a longo prazo. O livro mais prático sobre hábitos que já li!"),
        ("bruno", Decimal("4.0"), "Sistema claro, acionável e fundamentado na psicologia comportamental para criar e manter rotinas."),
    ],
    "9780812981605": [  # O Poder do Hábito
        ("gabriela", Decimal("5.0"), "Explicação clara do loop deixa-rotina-recompensa e como reprogramar padrões automáticos da mente."),
        ("joao", Decimal("4.0"), "Estudos de caso envolventes que comprovam o impacto dos hábitos nas pessoas e grandes organizações."),
    ],
    "9781455586691": [  # Trabalho Focado
        ("joao", Decimal("5.0"), "Leitura essencial na era das distrações digitais. Cal Newport ensina a resgatar a concentração produtiva profunda."),
        ("gabriela", Decimal("4.0"), "Dicas valiosas para organizar o dia e produzir trabalhos significativos sem dispersar o foco."),
    ],
    "9780345472328": [  # Mindset
        ("gabriela", Decimal("4.0"), "A distinção entre mentalidade fixa e de crescimento transforma a forma como encaramos fracassos e aprendizado."),
        ("elisa", Decimal("4.0"), "Inspirador para estudantes e profissionais que querem cultivar resiliência e evolução contínua."),
    ],
    "9781439167342": [  # Como Fazer Amigos e Influenciar Pessoas
        ("bruno", Decimal("5.0"), "Clássico atemporal sobre empatia, escuta ativa e relacionamentos humanos saudáveis e respeitosos."),
        ("ana", Decimal("4.0"), "Princípios simples de gentileza e consideração ao próximo que nunca perdem a relevância."),
    ],
    "9781612680194": [  # Pai Rico, Pai Pobre
        ("diego", Decimal("4.0"), "Aborda educação financeira básica e a importância de criar ativos em vez de acumular passivos."),
        ("bruno", Decimal("3.0"), "Mudança de mentalidade em relação ao dinheiro, trabalho assalariado e independência financeira."),
    ],
    "9780060555665": [  # O Investidor Inteligente
        ("felipe", Decimal("5.0"), "A bíblia do investimento em valor. Benjamin Graham ensina a importância da margem de segurança."),
        ("joao", Decimal("4.0"), "Conceitos sólidos que ensinam a controlar emoções e manter disciplina nos mercados de capitais."),
    ],
    "9780804139298": [  # De Zero a Um
        ("joao", Decimal("5.0"), "Peter Thiel traz pensamentos contraintuitivos e instigantes sobre monopólios e inovação vertical."),
        ("felipe", Decimal("4.0"), "Criar algo do zero é muito mais valioso do que apenas copiar o que já foi validado por outros."),
    ],
    "9780307887894": [  # A Startup Enxuta
        ("joao", Decimal("5.0"), "O ciclo construir-medir-aprender e o conceito de MVP revolucionaram a criação de novos produtos digitais."),
        ("gabriela", Decimal("4.0"), "Framework prático para validar hipóteses rapidamente evitando desperdício de tempo e recursos."),
    ],

    # --- Computação / Didáticos ---
    "9780132350884": [  # Código Limpo
        ("joao", Decimal("5.0"), "Qualquer tolo pode escrever código que o computador entende. Bons programadores escrevem código que humanos entendem!"),
        ("felipe", Decimal("4.0"), "Princípios essenciais de nomes expressivos, funções pequenas e testes automatizados de qualidade."),
    ],
    "9780135957059": [  # O Programador Pragmático
        ("joao", Decimal("5.0"), "Conselhos atemporais de carreira e engenharia. Todo desenvolvedor deveria reler esta obra periodicamente."),
        ("diego", Decimal("4.0"), "Aborda desde ferramentas de trabalho até responsabilidade profissional com maestria indiscutível."),
    ],
    "9780201633610": [  # Padrões de Projeto
        ("joao", Decimal("5.0"), "A referência fundamental dos 23 padrões GoF. Um marco para arquitetura orientada a objetos."),
        ("felipe", Decimal("4.0"), "Vocabulário comum e soluções consolidadas para os problemas recorrentes de design de software."),
    ],
    "9780735619678": [  # Code Complete
        ("joao", Decimal("5.0"), "Enciclopédia indispensável da construção de software. Abrange do planejamento à depuração minuciosa."),
        ("heitor", Decimal("4.0"), "Steve McConnell compila as melhores práticas comprovadas pela indústria com rigor científico."),
    ],
    "9780134757599": [  # Refatoração
        ("joao", Decimal("5.0"), "Martin Fowler ensina a arte de aperfeiçoar o design interno de sistemas sem alterar seu comportamento externo."),
        ("felipe", Decimal("4.0"), "Catálogo prático de 'code smells' e técnicas de refatoração passo a passo com testes sólidos."),
    ],
    "9780262046305": [  # Algoritmos: Teoria e Prática
        ("joao", Decimal("5.0"), "O livro-texto definitivo de algoritmos e estruturas de dados. Rigoroso, abrangente e indispensável."),
        ("felipe", Decimal("4.0"), "Leitura densa e desafiadora, mas serve como guia completo de consulta para qualquer cientista da computação."),
    ],
    "9780262510875": [  # Estrutura e Interpretação de Programas de Computador
        ("joao", Decimal("5.0"), "Uma experiência quase mística sobre abstração, modelos computacionais e a essência da programação."),
        ("heitor", Decimal("4.0"), "Muda para sempre sua compreensão sobre como linguagens de programação e interpretadores funcionam."),
    ],

    # --- Literatura Brasileira ---
    "9788535914849": [  # Dom Casmurro
        ("ana", Decimal("5.0"), "Bentinho e seus olhos de ressaca. A ambiguidade magistral de Machado de Assis coloca o leitor como jurado."),
        ("carla", Decimal("5.0"), "Traiu ou não traiu? A genialidade reside no narrador não confiável e na prosa irônica incomparável."),
    ],
    "9788535911664": [  # Memórias Póstumas de Brás Cubas
        ("heitor", Decimal("5.0"), "Um defunto autor narrando a própria vida com pessimismo hilário e inovação formal revolucionária."),
        ("isabela", Decimal("5.0"), "O nascimento do realismo brasileiro. A dedicatória ao verme que primeiro roeu as frias carnes é genial."),
    ],
    "9788525406958": [  # Vidas Secas
        ("carla", Decimal("5.0"), "Prosa enxuta e cortante retratando a saga de Fabiano, Sinhá Vitória e a inesquecível cadela Baleia no sertão."),
        ("ana", Decimal("4.0"), "Denúncia social profunda e comovente sobre a aridez da terra e a desumanização pela miséria."),
    ],
    "9788535921953": [  # Capitães da Areia
        ("diego", Decimal("5.0"), "A juventude marginalizada de Salvador em um romance vibrante, lírico e carregado de afeto e protesto."),
        ("elisa", Decimal("4.0"), "Pedro Bala, Dora e os meninos do trapiche conquistam a empatia do leitor desde as primeiras páginas."),
    ],
    "9788520925867": [  # A Hora da Estrela
        ("isabela", Decimal("5.0"), "Macabéa e sua existência invisível no Rio de Janeiro. Clarice Lispector escreve com dolorosa delicadeza."),
        ("carla", Decimal("5.0"), "Reflexão profunda sobre a criação literária, miséria material e a dignidade secreta dos esquecidos."),
    ],
    "9788535908770": [  # O Cortiço
        ("carla", Decimal("5.0"), "O ápice do naturalismo brasileiro. As paixões humanas e a influência do meio social retratadas com vigor."),
        ("heitor", Decimal("5.0"), "Um mosaico social cru e dinâmico da vida comunitária no Rio de Janeiro do final do século XIX."),
    ],
    "9788535902778": [  # Grande Sertão: Veredas
        ("ana", Decimal("5.0"), "O sertão é o mundo. A reinvenção linguística de Guimarães Rosa e o monólogo de Riobaldo são monumentais."),
        ("heitor", Decimal("5.0"), "Uma das maiores obras-primas da língua portuguesa. Filosofia, amor, jagunçagem e o mistério da existência."),
    ],
    "9788508040872": [  # O Quinze
        ("carla", Decimal("5.0"), "Rachel de Queiroz publicou esta obra marcante com apenas vinte anos. A seca de 1915 tratada com sobriedade e dor."),
        ("ana", Decimal("4.0"), "A dignidade dos retirantes e o amor contido entre Conceição e Vicente marcam o romance regionalista."),
    ],
    "9788535912388": [  # Quarto de Despejo
        ("ana", Decimal("5.0"), "Carolina Maria de Jesus registra a fome e a luta diária na favela com lirismo cru e força documental única."),
        ("isabela", Decimal("5.0"), "Leitura urgente e obrigatória. A voz potente de uma escritora que transformou papel recolhido em arte imortal."),
    ],
    "9788525050489": [  # Macunaíma
        ("bruno", Decimal("4.0"), "O herói sem nenhum caráter reúne a riqueza mitológica, linguística e folclórica do modernismo brasileiro."),
        ("isabela", Decimal("4.0"), "Raia a aurora e a inventividade verbal de Mário de Andrade deslumbra quem aprecia a brasilidade viva."),
    ],
}


def ensure_seed_users(password=DEFAULT_PASSWORD):
    """Cria ou recupera os 10 usuários padronizados com seus Profiles."""
    User = get_user_model()
    users = {}
    for username in SEED_USERS:
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_user(
                username=username,
                email=f"{username}@colecture.test",
                password=password,
            )
        if not Profile.objects.filter(user=user).exists():
            AccountService.create_account(user)
        users[username] = user
    return users


@transaction.atomic
def seed_reviews_for_books(stdout=None, style=None, update=False, default_password=DEFAULT_PASSWORD):
    """Gera resenhas e notas para todos os livros do catálogo.

    Garante que:
    1. Os livros presentes em BOOK_REVIEWS recebam suas resenhas com autores definidos.
    2. Qualquer livro adicional já cadastrado no banco que não possua resenha receba
       ao menos uma avaliação de leitor.
    3. O comando seja 100% idempotente (respeitando a restrição única book + user).

    Retorna um dicionário com estatísticas de criação.
    """
    users = ensure_seed_users(password=default_password)
    created = 0
    updated = 0
    skipped = 0

    # 1. Popula as resenhas curadas mapeadas por ISBN
    for isbn, reviews in BOOK_REVIEWS.items():
        book = Book.objects.filter(isbn=isbn).first()
        if not book:
            continue

        for username, rating, text in reviews:
            user = users.get(username)
            if not user:
                continue

            review_obj, was_created = BookReview.objects.get_or_create(
                book=book,
                user=user,
                defaults={
                    "rating": rating,
                    "review": text[:300],
                },
            )

            if was_created:
                created += 1
            elif update:
                review_obj.rating = rating
                review_obj.review = text[:300]
                review_obj.save()
                updated += 1
            else:
                skipped += 1

    # 2. Garante que nenhum livro do catálogo fique sem ao menos uma resenha
    # (caso existam livros criados fora do catálogo padrão de BOOK_REVIEWS)
    all_books = Book.objects.all()
    user_keys = list(users.keys())
    user_count = len(user_keys)

    for idx, book in enumerate(all_books):
        if not book.reviews.exists():
            assigned_username = user_keys[idx % user_count]
            assigned_user = users[assigned_username]
            default_text = (
                f"Uma leitura envolvente e rica em reflexões. "
                f"Recomendo a todos que apreciam obras do gênero {book.genre or 'geral'}."
            )
            BookReview.objects.get_or_create(
                book=book,
                user=assigned_user,
                defaults={
                    "rating": Decimal("4.0"),
                    "review": default_text[:300],
                },
            )
            created += 1

    total_reviewed_books = Book.objects.filter(reviews__isnull=False).distinct().count()

    stats = {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total_books_reviewed": total_reviewed_books,
    }

    if stdout:
        stdout.write(
            f"Avaliações: {created} criada(s), {updated} atualizada(s), "
            f"{skipped} já existente(s). Total de livros com resenhas: {total_reviewed_books}."
        )

    return stats
