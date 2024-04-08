"""corpus_freeze.py"""

from asyncio import run
from asyncio.subprocess import PIPE
from base64 import b64encode
from json import dump, load
from lzma import compress
from os import environ
from pathlib import Path
from sys import argv

from asyncio_as_completed import as_completed
from asyncio_cmd import git_cmd, main
from corpus_ascii import is_ascii
from corpus_utils import c_tqdm, corpus_objects

BAD_KEYS = frozenset((
    "00139b023f0791bc6273e11fec8e2b46848fde2f",
    "04df8bdbf14b8ea62f24fa13e70d2f8ca716ef26",
    "04f4f9aec305fb2a12b67c0625730235b70eb0d3",
    "0546b04d165a5bf39ea09f20ec61ba672b7244e0",
    "088c5a685f1ee48dc52ac629e48b9975b84f588c",
    "0a39a1f01f65ba8f13019fc60b8536887e23b6bc",
    "0d9692817b85ba09ee351f9287b4cea24b5a7f39",
    "0f8e0c69d4350299e68988d8079d1443949d3eb5",
    "14dcfc839d8ff262b367e24fc0f1216abf13b9b2",
    "1a7c3c4089a70001635accd83e4e704138218235",
    "1b718fd6dcce6c80137f102dfbbb96adc357bb25",
    "1bfbaa6ce0c46625e6e9199a4b8acaf6034558da",
    "1c5f59b37dd87130525711282a6679c84d11ba7d",
    "1d4fa4d9b67969835a5be4adba588642bbcab8b3",
    "1da5676d5a2c2bc7afdb1bc0725b8fe09d9b0e7f",
    "1dd4b07cb39d0c75528aced4a861881cb4346d3b",
    "1e445d9da094d2116c048d181b9d6247f497da6e",
    "1ea3f2207c7c8f41cf27b4864506c02ec79b4d24",
    "21e8bb7646e5f103a2e9268c1dad25a85abc958e",
    "220f46e2f866217f50a3f46fcdc2e089b4742eb5",
    "22ca0005f6b02d9a836ca283f185388e74953c65",
    "23ec38b8212159d7c9942758174df759401b54e3",
    "26869b184733bbbe524bc40c32c5c5f3dcd79f7a",
    "27951fe41310e38e38637e0de91bbd2468e080f6",
    "27c8cfa4b4dd29b4a0bd983f2acea315513f25ac",
    "27fc6434e423c873f88ed3d3bd5d28e7c9836a6e",
    "2945c6fbf47f5e153f2a6366c67da660cd80d991",
    "2a2800ccd3eef00664a247c351a648493f380b5a",
    "2b8c78bffa170220cb375e12c514da0f22facbff",
    "2ba86f588202f2c8b42a367608bd42f8b90163a6",
    "2be24065ccf5784799712ad95fc683806e62badc",
    "2ef60831cf9d4773c230b2813b45510b5140b8ba",
    "33f08c3612da51682e9867820aa8aa18adbed72d",
    "3445b56c222fb54c6b0aaef7ae5a192ab6c9cb55",
    "3465bcd2d1d4985880d2c4605bdb28d1861e2170",
    "355329a06995a5f07918e78368e9e71ac8a32938",
    "3a814cc440c7f2db306065b94a6213620e3ebe6b",
    "3baebce0c291ac8989c4461a5b646418ac6bd148",
    "3da645f7d20cb3284d70408de849ac8886446c0e",
    "400c95df9b81c27988bc61fc0bbbbd3d77f8867e",
    "407576f9dbfe42d531a024a18de4b8aa5ace7875",
    "42f39a29f7d18163abe16da10fd51d70091c2fa8",
    "456afa5f8cd1347aa7ffc4b526c7517a6b8fbc6b",
    "4763681342557351a0312fa645836235bcbe85e0",
    "484ddd87814b153222794fe81eccb6b1a229c26d",
    "4b51e22e7aac165da290f2ff0d5edd2f4243007a",
    "4c81fbee72e05ccfae3d047ae5f1d9c5c85bfe3d",
    "4c8b5364cfa29a8a932c60061863c327aea88cce",
    "4cfa18b9adf743fc862111c69f988e2193bb4d4c",
    "4f636b20e507500c6c53ecec09394b008dd07fc8",
    "4fc9701c8f6287d80dff3381dbd1e3896161b80e",
    "501b2f3bbc8a57c52997f45e6ebe31d24e5a6007",
    "5107f7715b008af0457902fb74bb1402bd869bba",
    "522e230e5faf8c38373405bf70a3ad73511ecefb",
    "55883d77efc6edfcfad364a36e69b08a798f3165",
    "56698b0690a5c854fe59679d938f43c87226cc65",
    "578b3721a4abc1ba22bd875b86b79ada2358f20b",
    "57dbba4088f74f545e05a68099d161a0b9d097e6",
    "57fcf0cafa04129ac1f3884aa9f664be2a16b277",
    "5875a1f00d22807731af954945ff86bd828b8c64",
    "59a2511bb2417a144234ee91cb6354e516d1225e",
    "59b375516712d260e2af23c68c299a97b61f9f3c",
    "59c4639e36da5e869f4ed89f9f697afc8ca47097",
    "5ea178c1d492f036687d3ca5e66a4892a4dc86c6",
    "6318d20c5f8ed3783f7c54bd2e566359b2b1dcef",
    "664e06c5cac1e75ac63ce5daca696309cfcb946c",
    "68dd57c21cb3d67b395e317f3d51ac155ba8f0da",
    "6a90d957df2f704ac73d5f1b5f2f793883bef4b6",
    "6f4137bdf068001881a685096e71a7703a55069c",
    "717268ce53923be0bc68ead914594307a0ae26fe",
    "74179c622eb99aabe6ee1acbce56238e5f01b040",
    "75a0cd33bdb74c586fe17e5663716ad30d33bf2d",
    "77fe716ae76ed2faecad194722ca5ea479685b32",
    "782f9f0dffaa93b84f4ded1b2051486f7f454986",
    "7a3af6902ce484db71f9efdc44c1a8bc53b33ebe",
    "7da54a85b6f231137cdd8f61431bbb36f3f593ff",
    "7e5063e0362731fc8c7002318fe5d3449fdae06a",
    "80cb31effafeb4d5adbf9df666b473a3fe0ab170",
    "80e6bc74943539143b8a821e1aa56db4e32ffa26",
    "81b02f29ef97d3388533e592169051dbb4f4b58b",
    "83390c04f66cdc781bfc6490a76ffadb25f634ef",
    "864c85a1aff96a1940db8942c5e7e921d2363c3d",
    "869d309bd9221a025d4a4c9e52b5246dbbd1fea0",
    "8bfcc0d0459138bb64a25a1c790c90dde50bff37",
    "8cfcca9d7dff1bd1efda2ca80890e8432e4af36c",
    "8d0c81108005d1e0a9495790861d8c659ac51a3d",
    "8e3155f7ce078c84be9463228f502d535f21871b",
    "909fffef34fd9db4dc5a9c1f66b33826f0436fd9",
    "916d5957c8f977879abd67367404df48bd5a10ad",
    "91c9dc646b35157e51a2a2c65e57817f1b1f9584",
    "929ff11f3aa5bc98b19b6858b0945d25ab59a6c8",
    "93e04ecec0f32fac1f7a89905ab35f242544661c",
    "95b1d8d48972d4cd40d0941db9b960596c87a297",
    "985ee2133c90d4e6d974fa47ddf5fd8721bbfce2",
    "98916f42f4afcb6072c48d31b85438aef5f6866f",
    "9929b5fdaa9e9d9ebba7abce429c9cd59ab365b8",
    "9e576a25691fa16417d0ff729022650bc224435f",
    "a08f17c840de43e2b6ef94fe5f55fcadf79e8a3f",
    "a0f0328d0f911261f197efa91643742a01ddbf2a",
    "a12e353f89b5067e636711064f450df744846d5e",
    "a23ea7021107ed9e49d90c6fcb136291d8c73914",
    "a353f56206484b45fe124c05270ce01adb886166",
    "a4ce3a58cd59a09f8090a0cb1d6eb64125b40d17",
    "ab72dd4e378e5f7f8b58df485b40a84da21121df",
    "ae498cf604d228a93a6f86f60f9719f2598f4f52",
    "af7fa358bc47be3966feee502f2c62a39856711f",
    "b11a5765dcd23411b176ecb1908649e0698f29ff",
    "b123a70b514d194b7435181abe6632db8b75f050",
    "b4345fb967cffbf09413779c0090ddf56c1c7364",
    "b54b78ac3b940c9985e37b2c319284cbfdd81c69",
    "b578de17745a5f0a5c18235f8f54a3a28436942d",
    "b63eabb56a5ac943c29d0ff631f360c4c4c874d4",
    "b7a7d3648bb36ece1385a8eee2f675e8cd4786bb",
    "bb54c1eecea1663c676ae6807b1273edd83337af",
    "bbc48920cfa0952a92ec65b829f986d6ca7d7a81",
    "bdfe3af34ef5b04fe5cee3950f3bfc4f4003a22a",
    "c193600f18613f0fe079f89f0f0a39419fe30692",
    "c3ce76b2b30213f579ecccf5653639a35402c61c",
    "c858b2d852852828f03c386e690ab3d6c707c0d7",
    "c8a22fdd932b8bf393a51b7def69d1b87bb7da89",
    "c8ef8f7bb2ba9c7c59595f698ed96366ac3c1e41",
    "cb1a33ea8865f506e53806af386c5de8e6589907",
    "cb4eeb9de7549ec673a2637d260ea1cd0ebf24a8",
    "cb765eea226d3e636ad1f925143321d8bdfe7fc4",
    "cfc10c12fecb683c8678e89a72bd3eeec50871f2",
    "d20f32af5e154cdc0f6ad21f8dd5ea5949bc781c",
    "d5e18ac0f04e9bc26d4107e0596686905f6711e4",
    "d6adbf067cf542805290c59af6bc204ecec6ac12",
    "d6b8903dde20c3edbe18f05062fadefd3453b28c",
    "d795fc6a1cd5f7f59bdb179cec04b36d3d9091d2",
    "d8314a8e49fd591c1e7e45eb8388e7306743f0ce",
    "dbd01c125f47f0744441d187a02639ead337559b",
    "ddf8d93b7bc81b43d9676bd67fae64fe82a05c41",
    "de2e4a649d4b6745c4a7cb9d4e42d2d3acff5faf",
    "de50cca079e86f22b76a98b0536534c4c4a6a3d1",
    "e13053a4c8773c8735bb00167a7ecb86a4f1e58c",
    "e3f1713ee7603fe6579b0742940ebba46606f061",
    "e44bab45682c9c6c7214ecdeb32990bc50c9fe5f",
    "e46d28e1febc1210412a136fb7bb5f259b588aef",
    "e6ec9f0da1d0b797df002e4bc52b17707a9d21cc",
    "e85f588bab00c34b64bfb51a0bd12d3dde2d8357",
    "e9896ea0c89eab28efa9a8b18b852d901c34d30a",
    "ecdcc96b040712710770fb5038d2ef22f16599f5",
    "ee0df6cb82c7162a85c1a3c7a2ee0e2fcc5af9dc",
    "ee801b14e46d5462ac7b0f148a5386dbf02e13e3",
    "efdefcd17bbb603e60f39f72d356793c1aac6b6b",
    "f11d4fde52d462a0fd66799b952d2057df4425b2",
    "f14433fd5cd6c013a45963078b5a378f566cff00",
    "f20adff428459d7f3d4dc886ddd7ab5ac79f238b",
    "f444f0001db368b49cbff67c9b2568943b59c758",
    "fb664b3a5373c56f5e48515e8b78dab061bfc93e",
    "fc841b1786ad3ba81c3f12a27932371e3e7c8631",
    "fd37ab180df504531539224c029858aedac66d5a",
    "feeb32cc51d9a47522d9b0fecea2c43cd1098b37",
))


async def corpus_freeze(
    output: str,
    *,
    base_reference: str = environ.get("BASE_REF", "HEAD"),
    disable_bars: bool | None,
) -> None:
    file = Path(output)
    with file.open() as istream:
        cases = {key: value for key, value in load(istream).items()}
    crashes = [
        path for path in Path("unit_tests/fuzz/crashes").rglob("*") if path.is_file()
    ]
    existing = frozenset(
        key.strip().decode()
        for key in await as_completed(
            c_tqdm(
                (git_cmd("hash-object", path, out=PIPE) for path in crashes),
                "Hash corpus",
                disable_bars,
                total=len(crashes),
            )
        )
    )
    for key in BAD_KEYS.union(existing).intersection(cases.keys()):
        del cases[key]
    cases.update(
        (sha, b64encode(compress(obj)).decode())
        for sha, obj in await corpus_objects(
            "unit_tests/fuzz/corpus",
            "unit_tests/fuzz/crashes",
            base_reference=base_reference,
            disable_bars=disable_bars,
            exclude=BAD_KEYS.union(existing).union(cases.keys()),
        )
        if is_ascii(obj)
    )
    with file.open("w") as ostream:
        dump(cases, ostream, indent=4, sort_keys=True)


async def corpus_freeze_main(output: str) -> None:
    await corpus_freeze(output, disable_bars=None)


if __name__ == "__main__":
    with main():
        run(corpus_freeze_main(*argv[1:]))
