"""Popula o catálogo com livros reais.

Uso:
    python manage.py seed_books              # insere os livros que ainda não existem
    python manage.py seed_books --no-covers  # insere sem URL de capa
    python manage.py seed_books --update     # também atualiza livros já existentes (mesmo ISBN)

O comando é idempotente: o ISBN é a chave, então rodá-lo várias vezes
não cria duplicatas.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from books.models import Book

COVER_URL = "https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"

# Os gêneros usam as mesmas chaves do GENRE_CHOICES de books/forms.py
# (ficcao, romance, fantasia, misterio, biografia, historia, autoajuda,
# didatico, outros), para o formulário de edição selecionar o valor certo.
#
# (isbn, título, autor, gênero, ano, páginas, editora, sinopse)
BOOKS = [
    # --- Ficção científica ---
    ("9780451524935", "1984", "George Orwell", "ficcao", 1949, 328, "Signet Classics",
     "Em uma Oceania totalitária vigiada pelo Grande Irmão, Winston Smith arrisca tudo ao ousar pensar por conta própria e se apaixonar."),
    ("9780060850524", "Admirável Mundo Novo", "Aldous Huxley", "ficcao", 1932, 288, "Harper Perennial",
     "Numa sociedade dividida em castas e anestesiada pelo prazer, um 'selvagem' expõe o preço da felicidade fabricada."),
    ("9781451673319", "Fahrenheit 451", "Ray Bradbury", "ficcao", 1953, 249, "Simon & Schuster",
     "Guy Montag é bombeiro num mundo em que a função é queimar livros, até que passa a questionar a ordem que serve."),
    ("9780441172719", "Duna", "Frank Herbert", "ficcao", 1965, 688, "Ace",
     "No deserto de Arrakis, único lugar onde nasce a especiaria mais valiosa do universo, o jovem Paul Atreides encontra seu destino."),
    ("9780441569595", "Neuromancer", "William Gibson", "ficcao", 1984, 271, "Ace",
     "Um hacker decadente é recrutado para uma invasão impossível no ciberespaço, em obra fundadora do cyberpunk."),
    ("9780812550702", "O Jogo do Exterminador", "Orson Scott Card", "ficcao", 1985, 324, "Tor Books",
     "Andrew 'Ender' Wiggin é treinado desde criança numa escola de guerra espacial para enfrentar uma ameaça alienígena."),
    ("9780553293357", "Fundação", "Isaac Asimov", "ficcao", 1951, 255, "Bantam Spectra",
     "Com o declínio do Império Galáctico à vista, o psico-historiador Hari Seldon cria um plano para encurtar a era de trevas."),
    ("9780345391803", "O Guia do Mochileiro das Galáxias", "Douglas Adams", "ficcao", 1979, 193, "Del Rey",
     "Pouco antes de a Terra ser demolida, Arthur Dent é arrastado numa viagem hilária pelo espaço com um guia eletrônico."),
    ("9780385333849", "Matadouro 5", "Kurt Vonnegut", "ficcao", 1969, 275, "Dial Press",
     "Billy Pilgrim se desprende do tempo e revisita o bombardeio de Dresden em uma sátira antiguerra."),
    ("9780385490818", "O Conto da Aia", "Margaret Atwood", "ficcao", 1985, 311, "Anchor Books",
     "Em Gilead, regime teocrático e misógino, Offred é forçada a servir como aia para gerar filhos à elite."),
    ("9780486282114", "Frankenstein", "Mary Shelley", "ficcao", 1818, 166, "Dover Publications",
     "O cientista Victor Frankenstein dá vida a uma criatura e precisa lidar com as consequências de brincar de Deus."),
    ("9780345539434", "Cosmos", "Carl Sagan", "didatico", 1980, 396, "Ballantine Books",
     "Carl Sagan conduz uma viagem pela história da astronomia e pelo lugar da humanidade no universo."),

    # --- Fantasia ---
    ("9780547928227", "O Hobbit", "J. R. R. Tolkien", "fantasia", 1937, 300, "Mariner Books",
     "Bilbo Bolseiro, um hobbit caseiro, une-se a treze anões e ao mago Gandalf numa jornada para recuperar um tesouro guardado por um dragão."),
    ("9780618346257", "A Sociedade do Anel", "J. R. R. Tolkien", "fantasia", 1954, 423, "Houghton Mifflin",
     "Frodo herda um anel perigoso e parte com uma companhia de nove para destruí-lo na Montanha da Perdição."),
    ("9780590353427", "Harry Potter e a Pedra Filosofal", "J. K. Rowling", "fantasia", 1997, 309, "Scholastic",
     "Aos onze anos, Harry descobre ser bruxo e é levado a Hogwarts, onde começa a desvendar o mistério de sua origem."),
    ("9780553593716", "A Guerra dos Tronos", "George R. R. Martin", "fantasia", 1996, 694, "Bantam Spectra",
     "Casas nobres de Westeros disputam o Trono de Ferro enquanto uma ameaça antiga desperta além da Muralha."),
    ("9780756404741", "O Nome do Vento", "Patrick Rothfuss", "fantasia", 2007, 662, "DAW Books",
     "Kvothe, lenda viva, conta sua própria história: do menino artista de trupe ao aluno prodígio da Universidade."),
    ("9780439023528", "Jogos Vorazes", "Suzanne Collins", "fantasia", 2008, 374, "Scholastic Press",
     "Katniss Everdeen se voluntaria para um espetáculo televisionado em que jovens lutam até a morte."),
    ("9780060934347", "Dom Quixote", "Miguel de Cervantes", "romance", 1605, 940, "Ecco",
     "Um fidalgo enlouquecido pelas novelas de cavalaria sai pelo mundo como cavaleiro andante, acompanhado do fiel Sancho Pança."),
    ("9780156012195", "O Pequeno Príncipe", "Antoine de Saint-Exupéry", "fantasia", 1943, 96, "Harcourt",
     "Um piloto perdido no deserto encontra um menino vindo de outro planeta e aprende com ele sobre amizade e o essencial."),

    # --- Romance / literatura clássica ---
    ("9780743273565", "O Grande Gatsby", "F. Scott Fitzgerald", "romance", 1925, 180, "Scribner",
     "Nick Carraway narra a obsessão do milionário Jay Gatsby por Daisy na Nova York dos anos 1920."),
    ("9780141439518", "Orgulho e Preconceito", "Jane Austen", "romance", 1813, 480, "Penguin Classics",
     "Elizabeth Bennet e o orgulhoso Sr. Darcy precisam superar a presunção e os preconceitos para se entenderem."),
    ("9780141441146", "Jane Eyre", "Charlotte Brontë", "romance", 1847, 532, "Penguin Classics",
     "Órfã e governanta, Jane se apaixona pelo misterioso Sr. Rochester em Thornfield Hall, que guarda um segredo."),
    ("9780141439556", "O Morro dos Ventos Uivantes", "Emily Brontë", "romance", 1847, 416, "Penguin Classics",
     "A paixão destrutiva entre Heathcliff e Catherine atravessa gerações nos ermos de Yorkshire."),
    ("9780142437247", "Moby Dick", "Herman Melville", "romance", 1851, 720, "Penguin Classics",
     "O capitão Ahab leva o baleeiro Pequod numa perseguição obsessiva à baleia branca que lhe tirou a perna."),
    ("9780143107637", "Crime e Castigo", "Fiódor Dostoiévski", "romance", 1866, 576, "Penguin Classics",
     "O estudante Raskólnikov comete um assassinato e é consumido pela culpa em São Petersburgo."),
    ("9780374528379", "Os Irmãos Karamázov", "Fiódor Dostoiévski", "romance", 1880, 824, "Farrar, Straus and Giroux",
     "Um parricídio expõe os dilemas de fé, liberdade e culpa de três irmãos e seu pai."),
    ("9780143035008", "Anna Karenina", "Liev Tolstói", "romance", 1877, 864, "Penguin Classics",
     "O caso de Anna com o conde Vronski escandaliza a aristocracia russa, em contraponto ao casamento de Kitty e Levin."),
    ("9781400079988", "Guerra e Paz", "Liev Tolstói", "romance", 1869, 1296, "Vintage Classics",
     "Cinco famílias aristocráticas russas vivem as guerras napoleônicas em um dos maiores romances da literatura."),
    ("9780451419439", "Os Miseráveis", "Victor Hugo", "romance", 1862, 1463, "Signet Classics",
     "O ex-prisioneiro Jean Valjean tenta reconstruir a vida enquanto é perseguido pelo inspetor Javert."),
    ("9780060883287", "Cem Anos de Solidão", "Gabriel García Márquez", "romance", 1967, 417, "Harper Perennial",
     "A saga da família Buendía na fictícia Macondo, entre o realismo e o fantástico, ao longo de sete gerações."),
    ("9780316769488", "O Apanhador no Campo de Centeio", "J. D. Salinger", "romance", 1951, 277, "Little, Brown",
     "Holden Caulfield vaga por Nova York após ser expulso da escola, em um retrato da alienação adolescente."),
    ("9780061120084", "O Sol é Para Todos", "Harper Lee", "romance", 1960, 336, "Harper Perennial",
     "Na Alabama dos anos 1930, a pequena Scout assiste ao pai, o advogado Atticus Finch, defender um homem negro injustamente acusado."),
    ("9780399501487", "O Senhor das Moscas", "William Golding", "romance", 1954, 208, "Perigee",
     "Meninos náufragos numa ilha deserta criam uma sociedade que logo degenera em violência."),
    ("9780451526342", "A Revolução dos Bichos", "George Orwell", "romance", 1945, 112, "Signet Classics",
     "Os animais de uma fazenda expulsam o dono, mas a nova ordem igualitária é corrompida pelos porcos."),
    ("9781451626650", "Ardil-22", "Joseph Heller", "romance", 1961, 544, "Simon & Schuster",
     "O capitão Yossarian tenta escapar das missões aéreas da Segunda Guerra, preso numa lógica burocrática absurda."),
    ("9781400033416", "Amada", "Toni Morrison", "romance", 1987, 324, "Vintage",
     "Sethe, ex-escravizada, é assombrada pelo fantasma da filha que matou para livrá-la da escravidão."),
    ("9780062315007", "O Alquimista", "Paulo Coelho", "romance", 1988, 208, "HarperOne",
     "O pastor andaluz Santiago viaja ao Egito em busca de um tesouro e descobre que o caminho importa mais que o destino."),
    ("9780486411095", "Drácula", "Bram Stoker", "misterio", 1897, 418, "Dover Publications",
     "O advogado Jonathan Harker viaja à Transilvânia e desperta o conde Drácula, que parte rumo a Londres."),

    # --- Mistério / suspense ---
    ("9780062073488", "E Não Sobrou Nenhum", "Agatha Christie", "misterio", 1939, 272, "William Morrow",
     "Dez desconhecidos são convidados a uma ilha e passam a ser mortos um a um, seguindo uma cantiga infantil."),
    ("9780062693662", "Assassinato no Expresso do Oriente", "Agatha Christie", "misterio", 1934, 288, "William Morrow",
     "Preso pela neve, o trem de luxo vira cenário de um crime que Hercule Poirot precisa resolver entre os passageiros."),
    ("9780307474278", "O Código Da Vinci", "Dan Brown", "misterio", 2003, 454, "Anchor",
     "Um assassinato no Louvre leva o simbologista Robert Langdon a uma trilha de enigmas sobre o Santo Graal."),
    ("9780307588371", "Garota Exemplar", "Gillian Flynn", "misterio", 2012, 432, "Crown",
     "No dia do aniversário de casamento, Amy desaparece e todas as suspeitas recaem sobre o marido, Nick."),
    ("9780307454546", "Os Homens que Não Amavam as Mulheres", "Stieg Larsson", "misterio", 2005, 644, "Vintage Crime",
     "O jornalista Mikael Blomkvist e a hacker Lisbeth Salander investigam um desaparecimento ocorrido décadas antes."),

    # --- Biografia / memórias ---
    ("9780553296983", "O Diário de Anne Frank", "Anne Frank", "biografia", 1947, 283, "Bantam",
     "Os registros de uma adolescente judia escondida em Amsterdã durante a ocupação nazista."),
    ("9780316548182", "Long Walk to Freedom (Longo Caminho para a Liberdade)", "Nelson Mandela", "biografia", 1994, 656, "Little, Brown",
     "A autobiografia de Mandela, da infância rural à luta contra o apartheid e à presidência da África do Sul."),
    ("9781451648539", "Steve Jobs", "Walter Isaacson", "biografia", 2011, 656, "Simon & Schuster",
     "A biografia autorizada do cofundador da Apple, baseada em dezenas de entrevistas com ele e com quem o conheceu."),
    ("9780399590504", "Educated (A Menina da Montanha)", "Tara Westover", "biografia", 2018, 352, "Random House",
     "Criada por uma família survivalista sem ir à escola, Tara chega a Cambridge e redescobre a própria história."),
    ("9781524763138", "Minha História", "Michelle Obama", "biografia", 2018, 448, "Crown",
     "Memórias da ex-primeira-dama dos Estados Unidos, de sua infância em Chicago à Casa Branca."),
    ("9780807014295", "Em Busca de Sentido", "Viktor E. Frankl", "biografia", 1946, 184, "Beacon Press",
     "O psiquiatra relata sua experiência em campos de concentração e apresenta a logoterapia."),

    # --- História / ciências humanas ---
    ("9780062316097", "Sapiens: Uma Breve História da Humanidade", "Yuval Noah Harari", "historia", 2011, 464, "Harper Perennial",
     "Da Revolução Cognitiva à era digital, uma síntese da trajetória da espécie humana."),
    ("9780062464316", "Homo Deus", "Yuval Noah Harari", "historia", 2015, 464, "Harper Perennial",
     "Uma reflexão sobre o futuro da humanidade diante de biotecnologia, dados e inteligência artificial."),
    ("9780525512172", "21 Lições para o Século 21", "Yuval Noah Harari", "historia", 2018, 372, "Spiegel & Grau",
     "Ensaios sobre desafios do presente, como tecnologia, desinformação, trabalho e política."),
    ("9780393354324", "Armas, Germes e Aço", "Jared Diamond", "historia", 1997, 528, "W. W. Norton",
     "Por que certas sociedades dominaram outras? Diamond explica a desigualdade global por geografia e ambiente."),
    ("9780553380163", "Uma Breve História do Tempo", "Stephen Hawking", "didatico", 1988, 212, "Bantam",
     "Hawking apresenta ao grande público buracos negros, Big Bang e a busca por uma teoria unificada."),
    ("9780374533557", "Rápido e Devagar: Duas Formas de Pensar", "Daniel Kahneman", "didatico", 2011, 499, "Farrar, Straus and Giroux",
     "O Nobel de Economia descreve os dois sistemas de pensamento que moldam nossos julgamentos e decisões."),

    # --- Desenvolvimento pessoal / negócios ---
    ("9780735211292", "Hábitos Atômicos", "James Clear", "autoajuda", 2018, 320, "Avery",
     "Um método prático para criar bons hábitos e abandonar os ruins por meio de pequenas mudanças consistentes."),
    ("9780812981605", "O Poder do Hábito", "Charles Duhigg", "autoajuda", 2012, 400, "Random House",
     "Como os hábitos funcionam no cérebro, nas empresas e na sociedade, e como transformá-los."),
    ("9781455586691", "Trabalho Focado", "Cal Newport", "autoajuda", 2016, 304, "Grand Central Publishing",
     "Argumenta que a capacidade de concentração profunda é rara e valiosa, e propõe regras para cultivá-la."),
    ("9780345472328", "Mindset: A Nova Psicologia do Sucesso", "Carol S. Dweck", "autoajuda", 2006, 276, "Ballantine Books",
     "A pesquisadora distingue a mentalidade fixa da de crescimento e mostra como ela afeta o aprendizado."),
    ("9781439167342", "Como Fazer Amigos e Influenciar Pessoas", "Dale Carnegie", "autoajuda", 1936, 291, "Gallery Books",
     "Clássico sobre relacionamento interpessoal, com princípios de comunicação e persuasão."),
    ("9781612680194", "Pai Rico, Pai Pobre", "Robert T. Kiyosaki", "autoajuda", 1997, 336, "Plata Publishing",
     "Contrasta as lições sobre dinheiro de dois 'pais' e defende a educação financeira desde cedo."),
    ("9780060555665", "O Investidor Inteligente", "Benjamin Graham", "autoajuda", 1949, 640, "Harper Business",
     "Referência de investimento em valor, com os conceitos de margem de segurança e do Sr. Mercado."),
    ("9780804139298", "De Zero a Um", "Peter Thiel", "autoajuda", 2014, 224, "Crown Business",
     "Thiel defende que construir algo realmente novo vale mais do que competir no que já existe."),
    ("9780307887894", "A Startup Enxuta", "Eric Ries", "autoajuda", 2011, 336, "Crown Business",
     "Apresenta o ciclo construir-medir-aprender para validar ideias com rapidez e pouco desperdício."),

    # --- Computação / didáticos ---
    ("9780132350884", "Código Limpo", "Robert C. Martin", "didatico", 2008, 464, "Prentice Hall",
     "Princípios e exemplos para escrever código legível, simples e fácil de manter."),
    ("9780135957059", "O Programador Pragmático", "David Thomas; Andrew Hunt", "didatico", 2019, 352, "Addison-Wesley",
     "Dicas atemporais de ofício para quem quer evoluir como desenvolvedor de software."),
    ("9780201633610", "Padrões de Projeto", "Erich Gamma; Richard Helm; Ralph Johnson; John Vlissides", "didatico", 1994, 395, "Addison-Wesley",
     "Catálogo de 23 padrões de projeto orientado a objetos, obra da chamada 'Gangue dos Quatro'."),
    ("9780735619678", "Code Complete", "Steve McConnell", "didatico", 2004, 960, "Microsoft Press",
     "Guia abrangente de construção de software, da codificação a testes e depuração."),
    ("9780134757599", "Refatoração", "Martin Fowler", "didatico", 2018, 448, "Addison-Wesley",
     "Técnicas para melhorar o design de código existente sem alterar seu comportamento."),
    ("9780262046305", "Algoritmos: Teoria e Prática", "Thomas H. Cormen; Charles E. Leiserson; Ronald L. Rivest; Clifford Stein", "didatico", 2022, 1312, "MIT Press",
     "Livro de referência em algoritmos e estruturas de dados, usado em cursos de computação no mundo todo."),
    ("9780262510875", "Estrutura e Interpretação de Programas de Computador", "Harold Abelson; Gerald Jay Sussman", "didatico", 1996, 657, "MIT Press",
     "Clássico que ensina abstração, recursão e interpretação de programas usando Scheme."),

    # --- Literatura brasileira ---
    ("9788535914849", "Dom Casmurro", "Machado de Assis", "romance", 1899, 256, "Companhia das Letras",
     "Bentinho relata sua vida e a dúvida sobre a fidelidade de Capitu, sem que o leitor chegue a um veredito."),
    ("9788535911664", "Memórias Póstumas de Brás Cubas", "Machado de Assis", "romance", 1881, 272, "Companhia das Letras",
     "Brás Cubas, já morto, narra a própria vida com ironia e pessimismo."),
    ("9788525406958", "Vidas Secas", "Graciliano Ramos", "romance", 1938, 176, "Record",
     "A família do vaqueiro Fabiano migra pelo sertão nordestino fugindo da seca e da miséria."),
    ("9788535921953", "Capitães da Areia", "Jorge Amado", "romance", 1937, 280, "Companhia das Letras",
     "Meninos de rua de Salvador vivem de pequenos furtos em um trapiche abandonado."),
    ("9788520925867", "A Hora da Estrela", "Clarice Lispector", "romance", 1977, 88, "Rocco",
     "Macabéa, datilógrafa nordestina no Rio de Janeiro, é narrada por Rodrigo S. M. em seu cotidiano de privações."),
    ("9788535908770", "O Cortiço", "Aluísio Azevedo", "romance", 1890, 304, "Companhia das Letras",
     "A vida num cortiço carioca expõe as relações de ganância, raça e classe no século XIX."),
    ("9788535902778", "Grande Sertão: Veredas", "João Guimarães Rosa", "romance", 1956, 624, "Companhia das Letras",
     "O ex-jagunço Riobaldo conta sua trajetória pelo sertão e seu pacto com o diabo, em linguagem inventiva."),
    ("9788508040872", "O Quinze", "Rachel de Queiroz", "romance", 1930, 144, "José Olympio",
     "Durante a seca de 1915, a vida de retirantes cearenses se cruza com um amor difícil entre Conceição e Vicente."),
    ("9788535912388", "Quarto de Despejo", "Carolina Maria de Jesus", "biografia", 1960, 200, "Ática",
     "Diário de uma catadora de papel moradora da favela do Canindé, em São Paulo."),
    ("9788525050489", "Macunaíma", "Mário de Andrade", "romance", 1928, 224, "Nova Fronteira",
     "O 'herói sem nenhum caráter' percorre o Brasil em uma rapsódia modernista de mitos e folclore."),
]


def isbn13_is_valid(isbn: str) -> bool:
    """Confere o dígito verificador do ISBN-13."""
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn[:12]))
    return (10 - total % 10) % 10 == int(isbn[12])


class Command(BaseCommand):
    help = "Popula o catálogo de livros com títulos reais. Uso: python manage.py seed_books"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-covers", action="store_true",
            help="Não preenche a URL da capa (campo icon).",
        )
        parser.add_argument(
            "--update", action="store_true",
            help="Atualiza os dados de livros que já existem (mesmo ISBN).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created = updated = skipped = invalid = 0

        for isbn, title, author, genre, year, pages, publisher, synopsis in BOOKS:
            if not isbn13_is_valid(isbn):
                self.stdout.write(self.style.WARNING(f"ISBN inválido, ignorado: {isbn} ({title})"))
                invalid += 1
                continue

            defaults = {
                "title": title[:200],
                "author": author[:200],
                "genre": genre,
                "publish_year": year,
                "pages": pages,
                "publisher": publisher[:200],
                "synopsis": synopsis[:500],
                "icon": "" if options["no_covers"] else COVER_URL.format(isbn=isbn),
            }

            book, was_created = Book.objects.get_or_create(isbn=isbn, defaults=defaults)
            if was_created:
                created += 1
            elif options["update"]:
                for field, value in defaults.items():
                    setattr(book, field, value)
                book.save()
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Concluído: {created} criado(s), {updated} atualizado(s), "
            f"{skipped} já existente(s), {invalid} inválido(s)."
        ))