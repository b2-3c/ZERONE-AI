{
  description = "ZERONE AI - Your ultimate Waifu AI Assistant";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs, }:
    let
      overlay = import ./overlay.nix;
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      nixpkgsFor = forAllSystems (system: import nixpkgs { inherit system; config.allowUnfree = true; overlays = [ overlay ];  });
    in {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
          {
          zeroneai = pkgs.callPackage ./package.nix { };
        });

      defaultPackage = forAllSystems (system: self.packages.${system}.zeroneai);

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgsFor.${system};
        in
          {
          default = pkgs.mkShell {
            buildInputs = [
              self.packages.${system}.zeroneai
            ];
          };
        });
    };
}
