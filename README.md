# Sharp

**Sharp** — асинхронный кроссплатформенный инструмент для Minecraft-серверов.

**v1.1.0**

- **Windows / macOS / Linux**
- **Temurin JDK** — [Adoptium API](https://api.adoptium.net)
- **Paper** — [Fill API v3](https://fill.papermc.io)
- **Плагины и моды** — [Modrinth API](https://docs.modrinth.com/api/) (корректный User-Agent + обработка 429)
- Интерактивное меню + CLI
- Расширенные настройки `server.properties`

## Установка

```bash
git clone https://github.com/cizik5064-arch/Sharp.git
cd Sharp
pip install -r requirements.txt
python -m sharp
```

## Меню

```bash
sharp
# 1 Серверы · 2 Java · 3 Paper · 4 Плагины/моды · 5 Инфо
```

## CLI

```bash
sharp server create myserver --eula --memory 4G --difficulty normal
sharp server settings myserver --motd "Hello" --view-distance 12
sharp plugin search "essentials" -v 1.21.11
sharp plugin install myserver essentialsx
sharp plugin list myserver
sharp mod search sodium --loader fabric
sharp java install 21
sharp paper versions
```

## Modrinth

User-Agent: `cizik5064-arch/Sharp/1.1.0 (…; https://github.com/cizik5064-arch/Sharp)`  
Rate limit 300/min, retry on 429, SHA-512 verify.

## Лицензия

MIT
