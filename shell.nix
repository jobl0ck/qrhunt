let
  pkgs = import <nixpkgs> {};
in pkgs.mkShell {
  packages = with pkgs; [
    (python3.withPackages (p: with p; [
      p.flask
      p.qrcode
      p.pillow
    ]))
  ];
}